import json
import struct
import shutil
import numpy as np
from pathlib import Path
from py3dtiles.tileset.bounding_volume_box import BoundingVolumeBox
from lazExtractor import LAZExtractor

class TileGeneratorQuality:
    def __init__(self, max_points_per_tile: int = 30000, max_levels: int = 6):
        self.output_dir = Path("../3dTilesPointCloud/")
        self.max_points_per_tile = max_points_per_tile
        self.max_levels = max_levels
        self.tile_counter = 0
    
    def _criar_bounding_volume_from_points(self, pontos: np.ndarray) -> BoundingVolumeBox:
        # cria um BoundingVolumeBox a partir dos pontos
        min_coords = np.min(pontos, axis=0)
        max_coords = np.max(pontos, axis=0)
        center = (min_coords + max_coords) / 2.0
        half_axes = (max_coords - min_coords) / 2.0
        
        box_array = [
            center[0], center[1], center[2],
            half_axes[0], 0, 0,               
            0, half_axes[1], 0,              
            0, 0, half_axes[2]               
        ]
        
        return BoundingVolumeBox.from_list(box_array)
    
    def _escrever_tile_pnts(self, pontos: np.ndarray, cores: np.ndarray, filepath: Path):
        num_pontos = len(pontos)
        
        center = np.mean(pontos, axis=0)
        pontos_centrados = pontos - center
        
        feature_table_json = {
            "POINTS_LENGTH": num_pontos,
            "POSITION": {"byteOffset": 0},
            "RGB": {"byteOffset": num_pontos * 12},
            "RTC_CENTER": [float(center[0]), float(center[1]), float(center[2])]
        }
        
        # serializa json e adiciona padding
        ft_json_str = json.dumps(feature_table_json, separators=(',', ':'))
        ft_json_bytes = ft_json_str.encode('utf-8')
        ft_json_padding = (4 - len(ft_json_bytes) % 4) % 4
        ft_json_bytes += b' ' * ft_json_padding
        
        positions = pontos_centrados.astype(np.float32).tobytes()
        colors = np.clip(cores, 0, 255).astype(np.uint8).tobytes()
        ft_binary = positions + colors
        ft_binary_padding = (8 - len(ft_binary) % 8) % 8
        ft_binary += b'\x00' * ft_binary_padding
        
        # header
        magic = b'pnts'
        version = 1
        byte_length = 28 + len(ft_json_bytes) + len(ft_binary)
        ft_json_length = len(ft_json_bytes)
        ft_binary_length = len(ft_binary)
        
        with open(filepath, 'wb') as f:
            # header
            f.write(magic)
            f.write(struct.pack('<I', version))
            f.write(struct.pack('<I', byte_length))
            f.write(struct.pack('<I', ft_json_length))
            f.write(struct.pack('<I', ft_binary_length))
            f.write(struct.pack('<I', 0))
            f.write(struct.pack('<I', 0))  
            
            f.write(ft_json_bytes)
            f.write(ft_binary)
    
    def _dividir_pontos_octree(self, pontos: np.ndarray, cores: np.ndarray, bounds, nivel: int = 0) -> list:
        min_bounds, max_bounds = bounds
        center = (min_bounds + max_bounds) / 2.0
        
        octantes = []
        
        for i in range(8):
            oct_min = min_bounds.copy()
            oct_max = max_bounds.copy()
            
            if i & 1: oct_min[0] = center[0]
            else: oct_max[0] = center[0]
            
            if i & 2: oct_min[1] = center[1] 
            else: oct_max[1] = center[1]
            
            if i & 4: oct_min[2] = center[2]
            else: oct_max[2] = center[2]
            
            mask = np.all((pontos >= oct_min - 1e-6) & (pontos <= oct_max + 1e-6), axis=1)
            pontos_oct = pontos[mask]
            cores_oct = cores[mask]
            
            min_points_threshold = max(200, self.max_points_per_tile // (8 + nivel * 2))  # Threshold dinâmico baseado no nível
            if len(pontos_oct) >= min_points_threshold:
                octantes.append({
                    'pontos': pontos_oct,
                    'cores': cores_oct,
                    'bounds': (oct_min, oct_max)
                })
        
        return octantes
    
    def _construir_tiles_octree(self, pontos: np.ndarray, cores: np.ndarray, 
                               nivel: int = 0, bounds=None) -> dict:
        if bounds is None:
            min_coords = np.min(pontos, axis=0)
            max_coords = np.max(pontos, axis=0)
            padding = (max_coords - min_coords) * 0.001
            bounds = (min_coords - padding, max_coords + padding)
        
        bounding_volume = self._criar_bounding_volume_from_points(pontos)
        
        diagonal = np.linalg.norm(bounds[1] - bounds[0])
        
        if nivel <= 2:  # Níveis iniciais - mais conservador para performance
            base_error = diagonal * 1.5
            level_factor = 2.0 ** (-nivel * 0.3)
        else:  # Níveis detalhados - manter precisão para qualidade
            base_error = diagonal * 0.8
            level_factor = 2.0 ** (-nivel * 0.5)
        
        geometric_error = max(2.0, base_error * level_factor)     
        
        deve_criar_folha = (
            len(pontos) <= self.max_points_per_tile or
            nivel >= self.max_levels or
            geometric_error < 2.0                   
        )
        
        if deve_criar_folha:
            self.tile_counter += 1
            tile_filename = f"tile_{self.tile_counter}.pnts"
            tile_path = self.output_dir / tile_filename
            
            self._escrever_tile_pnts(pontos, cores, tile_path)
            
            return {
                "boundingVolume": bounding_volume.to_dict(),
                "geometricError": max(geometric_error, 1.0),
                "content": {"uri": tile_filename},
                "refine": "REPLACE"
            }
        else:
            octantes = self._dividir_pontos_octree(pontos, cores, bounds, nivel)
            
            if len(octantes) <= 1:
                self.tile_counter += 1
                tile_filename = f"tile_{self.tile_counter}.pnts"
                tile_path = self.output_dir / tile_filename
                
                self._escrever_tile_pnts(pontos, cores, tile_path)
                
                return {
                    "boundingVolume": bounding_volume.to_dict(),
                    "geometricError": max(geometric_error, 1.0),
                    "content": {"uri": tile_filename},
                    "refine": "REPLACE"
                }
            
            children = []
            for octante in octantes:
                if len(octante['pontos']) >= 400:                    
                    child = self._construir_tiles_octree(
                        octante['pontos'], 
                        octante['cores'],
                        nivel + 1,
                        octante['bounds']
                    )
                    children.append(child)
            
            tile_dict = {
                "boundingVolume": bounding_volume.to_dict(),
                "geometricError": geometric_error,
                "refine": "ADD"
            }
            
            if children:
                tile_dict["children"] = children
            
            return tile_dict
    
    def _verificar_tileset_existente(self) -> bool:
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            print("Pasta de output não existe")
            return False
        
        tileset_path = self.output_dir / "tileset.json"
        if not tileset_path.exists():
            print("Arquivo tileset.json não encontrado")
            return False
        
        try:
            with open(tileset_path, 'r') as f:
                tileset_data = json.load(f)
            
            if not all(key in tileset_data for key in ["asset", "geometricError", "root"]):
                print("Estrutura do tileset.json inválida")
                return False
            
            tiles_esperados = self._contar_tiles_no_tileset(tileset_data["root"])
            

            tiles_existentes = list(self.output_dir.glob("*.pnts"))
            
            if len(tiles_existentes) >= tiles_esperados and tiles_esperados > 0:
                print(f"Tileset válido encontrado: {len(tiles_existentes)} tiles")
                return True
            else:
                print(f"Tileset incompleto: {len(tiles_existentes)} tiles encontrados, {tiles_esperados} esperados")
                return False
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"Erro ao verificar tileset: {e}")
            return False
    
    def _contar_tiles_no_tileset(self, tile_node: dict) -> int:
        count = 0
        
        if "content" in tile_node and "uri" in tile_node["content"]:
            count += 1
        
        if "children" in tile_node:
            for child in tile_node["children"]:
                count += self._contar_tiles_no_tileset(child)
        
        return count
    
    def _limpar_diretorio_saida(self):
        if not self.output_dir.is_dir():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return

        print("Limpando diretório de saída...")
        for item_path in self.output_dir.iterdir():
            try:
                if item_path.is_file() or item_path.is_symlink():
                    item_path.unlink()
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Erro ao deletar {item_path}: {e}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def gerar_tileset(self, pontos: np.ndarray, cores: np.ndarray, forcar_regeneracao: bool = False) -> dict:

        print("Verificando tileset existente...")
        
        if not forcar_regeneracao and self._verificar_tileset_existente():
            print("Tileset válido encontrado! Carregando tileset existente...")
            tileset_path = self.output_dir / "tileset.json"
            with open(tileset_path, 'r') as f:
                tileset_existente = json.load(f)
            

            tiles_existentes = list(self.output_dir.glob("*.pnts"))
            self.tile_counter = len(tiles_existentes)
            print(f"Reutilizando tileset com {self.tile_counter} tiles existentes")
            
            return tileset_existente
        
        if forcar_regeneracao:
            print("Regeneração forçada - criando novo tileset...")
        else:
            print("Tileset não encontrado ou inválido - criando novo tileset...")
        
        print("Construindo árvore de tiles octree otimizada...")
        print(f"Configurações: {self.max_points_per_tile} pontos/tile, {self.max_levels} níveis máximos")
        
        self._limpar_diretorio_saida()
        
        self.tile_counter = 0
        
        tile_raiz = self._construir_tiles_octree(pontos, cores)
        
        min_coords = np.min(pontos, axis=0)
        max_coords = np.max(pontos, axis=0)
        diagonal_global = np.linalg.norm(max_coords - min_coords)
        geometric_error_global = diagonal_global * 0.6               
        
        tileset = {
            "asset": {"version": "1.0"},
            "geometricError": geometric_error_global,
            "root": tile_raiz
        }
        
        return tileset
    
    def salvar_tileset_json(self, tileset: dict):

        tileset_path = self.output_dir / "tileset.json"
        with open(tileset_path, 'w') as f:
            json.dump(tileset, f, indent=2)
        
        print(f"Tileset salvo em: {tileset_path}")
        print(f"Total de tiles criados: {self.tile_counter}")
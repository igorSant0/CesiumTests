import json
import struct
import shutil
import numpy as np
from pathlib import Path
from py3dtiles.tileset.bounding_volume_box import BoundingVolumeBox
from lazExtractor import LAZExtractor

class TileGenerator:
    
    def __init__(self, max_points_per_tile: int = 25000, max_levels: int = 6):
        self.output_dir = Path("/3dTiles/")
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
        # escreve um tile no formato .pnts
        num_pontos = len(pontos)
        
        feature_table_json = {
            "POINTS_LENGTH": num_pontos,
            "POSITION": {"byteOffset": 0},
            "RGB": {"byteOffset": num_pontos * 12}
        }
        
        # serializa json e adiciona padding
        ft_json_str = json.dumps(feature_table_json, separators=(',', ':'))
        ft_json_bytes = ft_json_str.encode('utf-8')
        ft_json_padding = (4 - len(ft_json_bytes) % 4) % 4
        ft_json_bytes += b' ' * ft_json_padding
        
        positions = pontos.astype(np.float32).tobytes()
        colors = cores.astype(np.uint8).tobytes()
        ft_binary = positions + colors
        ft_binary_padding = (8 - len(ft_binary) % 8) % 8
        ft_binary += b'\x00' * ft_binary_padding
        
        # header
        magic = b'pnts'
        version = 1
        byte_length = 28 + len(ft_json_bytes) + len(ft_binary)
        ft_json_length = len(ft_json_bytes)
        ft_binary_length = len(ft_binary)
        
        # escrev
        with open(filepath, 'wb') as f:
            # header
            f.write(magic)
            f.write(struct.pack('<I', version))
            f.write(struct.pack('<I', byte_length))
            f.write(struct.pack('<I', ft_json_length))
            f.write(struct.pack('<I', ft_binary_length))
            f.write(struct.pack('<I', 0))  # Batch Table JSON length
            f.write(struct.pack('<I', 0))  # Batch Table Binary length
            
            # Feature Table
            f.write(ft_json_bytes)
            f.write(ft_binary)
    
    def _dividir_pontos_octree(self, pontos: np.ndarray, cores: np.ndarray, bounds) -> list:
        min_bounds, max_bounds = bounds
        center = (min_bounds + max_bounds) / 2.0
        
        octantes = []
        
        for i in range(8):
            # define limites do octante
            oct_min = min_bounds.copy()
            oct_max = max_bounds.copy()
            
            if i & 1: oct_min[0] = center[0]
            else: oct_max[0] = center[0]
            
            if i & 2: oct_min[1] = center[1] 
            else: oct_max[1] = center[1]
            
            if i & 4: oct_min[2] = center[2]
            else: oct_max[2] = center[2]
            
            mask = np.all((pontos >= oct_min) & (pontos < oct_max), axis=1)
            pontos_oct = pontos[mask]
            cores_oct = cores[mask]
            
            if len(pontos_oct) > 0:
                octantes.append({
                    'pontos': pontos_oct,
                    'cores': cores_oct,
                    'bounds': (oct_min, oct_max)
                })
        
        return octantes
    
    def _construir_tiles_octree(self, pontos: np.ndarray, cores: np.ndarray, 
                               nivel: int = 0, bounds=None) -> dict:
        # construção recursiva
        if bounds is None:
            min_coords = np.min(pontos, axis=0)
            max_coords = np.max(pontos, axis=0)
            bounds = (min_coords, max_coords)
        
        bounding_volume = self._criar_bounding_volume_from_points(pontos)
        
        diagonal = np.linalg.norm(bounds[1] - bounds[0])
        geometric_error = diagonal / (2 ** nivel)
        
        deve_criar_folha = (
            len(pontos) <= self.max_points_per_tile or
            nivel >= self.max_levels or
            geometric_error < 10.0
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
            # tile pai -> divide em octantes
            octantes = self._dividir_pontos_octree(pontos, cores, bounds)
            
            if len(octantes) <= 1:
                # se não conseguiu dividi forçar criação de folha
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
            
            # cria tiles filhos recursivamente
            children = []
            for octante in octantes:
                if len(octante['pontos']) >= 100:
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
    
    def _limpar_diretorio_saida(self):
        """
        Limpa o conteúdo do diretório de saída sem apagar o próprio diretório.
        Isso evita o erro 'Device or resource busy' ao usar volumes Docker.
        """
        # Verifica se o diretório de saída realmente existe e é um diretório
        if not self.output_dir.is_dir():
            return  # Se não for um diretório, não há nada a fazer

        # Itera sobre cada item (arquivo, link ou subdiretório) DENTRO do diretório de saída
        for item_path in self.output_dir.iterdir():
            try:
                # Se for um arquivo ou link simbólico, apaga com unlink()
                if item_path.is_file() or item_path.is_symlink():
                    item_path.unlink()
                # Se for um subdiretório, apaga recursivamente com rmtree()
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Erro ao deletar {item_path}: {e}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def gerar_tileset(self, pontos: np.ndarray, cores: np.ndarray) -> dict:
        print("Construindo árvore de tiles octree...")
        
        self._limpar_diretorio_saida()
        
        tile_raiz = self._construir_tiles_octree(pontos, cores)
        
        tileset = {
            "asset": {"version": "1.0"},
            "geometricError": tile_raiz["geometricError"],
            "root": tile_raiz
        }
        
        return tileset
    
    def salvar_tileset_json(self, tileset: dict):
        tileset_path = self.output_dir / "tileset.json"
        with open(tileset_path, 'w') as f:
            json.dump(tileset, f, indent=2)
        
        print(f"Tileset salvo em: {tileset_path}")
        print(f"Total de tiles criados: {self.tile_counter}")
import json
import numpy as np
import laspy
from pathlib import Path
from pyproj import CRS, Transformer
from typing import Tuple, Dict

class LAZExtractor:
    def __init__(self, diretorio_ept: Path):
        self.diretorio_ept = diretorio_ept
        self.metadados = self._ler_metadados_ept()
        self.transformer = self._configurar_transformador()
    
    def _ler_metadados_ept(self) -> Dict:
        # le os metadados do EPT
        ept_json_path = self.diretorio_ept / "ept.json"
        if not ept_json_path.exists():
            raise FileNotFoundError(f"Arquivo ept.json não encontrado: {ept_json_path}")
        
        with open(ept_json_path, 'r') as f:
            return json.load(f)
    
    def _configurar_transformador(self) -> Transformer:
        # configura o transformador de coordenadas UTM para ECEF
        try:
            srs = self.metadados.get("srs", {})
            if "horizontal" in srs:
                utm_epsg = srs["horizontal"].replace("EPSG:", "")
                crs_utm = CRS.from_epsg(int(utm_epsg))
                crs_ecef = CRS.from_epsg(4978)  # ECEF
                return Transformer.from_crs(crs_utm, crs_ecef, always_xy=True)
            else:
                raise ValueError("EPSG não encontrado nos metadados EPT")
        except Exception as e:
            print(f"Erro ao configurar transformador: {e}")
            return None
    
    def _extrair_cores_las(self, las: laspy.LasData) -> np.ndarray:
        # extrai cores RGB do arquivo LAS/LAZ
        if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
            red = las.red
            green = las.green  
            blue = las.blue
            
            max_color = max(red.max(), green.max(), blue.max())
            
            if max_color > 255:
                # converte de 16-bit para 8-bit
                red = (red / 65535.0 * 255).astype(np.uint8)
                green = (green / 65535.0 * 255).astype(np.uint8)
                blue = (blue / 65535.0 * 255).astype(np.uint8)
            else:
                # está em 8-bit
                red = red.astype(np.uint8)
                green = green.astype(np.uint8)
                blue = blue.astype(np.uint8)
            
            cores = np.column_stack((red, green, blue))
            print(f"  Cores extraídas: formato {'16-bit' if max_color > 255 else '8-bit'} -> RGB 8-bit")
        else:
            print("  Aviso: arquivo não contém informações de cor, usando cor padrão (branco)")
            # Cor branca como padrão se não houver cores
            cores = np.full((len(las.points), 3), 255, dtype=np.uint8)
        
        return cores
    
    def _converter_coordenadas_para_ecef(self, pontos: np.ndarray) -> np.ndarray:
        # converte coordenadas UTM para ECEF
        if self.transformer is None:
            print("Aviso: Transformador não configurado, usando coordenadas originais")
            return pontos
        
        try:
            x_ecef, y_ecef, z_ecef = self.transformer.transform(
                pontos[:, 0], pontos[:, 1], pontos[:, 2]
            )
            return np.column_stack([x_ecef, y_ecef, z_ecef])
        except Exception as e:
            print(f"Erro na conversão para ECEF: {e}")
            return pontos
    
    def processar_arquivo_laz(self, arquivo_laz: Path) -> Tuple[np.ndarray, np.ndarray]:
        try:
            with laspy.open(arquivo_laz) as las_file:
                las = las_file.read()
                
                pontos = np.column_stack([las.x, las.y, las.z])
                
                pontos_ecef = self._converter_coordenadas_para_ecef(pontos)
                
                cores = self._extrair_cores_las(las)
                
                return pontos_ecef, cores
                
        except Exception as e:
            print(f"Erro ao processar {arquivo_laz}: {e}")
            return None, None
    
    def processar_todos_arquivos_laz(self) -> Tuple[np.ndarray, np.ndarray]:
        arquivos_laz = list(self.diretorio_ept.glob("**/*.laz"))
        
        if not arquivos_laz:
            raise ValueError(f"Nenhum arquivo LAZ encontrado em: {self.diretorio_ept}")
        
        todos_pontos = []
        todas_cores = []
        
        print(f"Encontrados {len(arquivos_laz)} arquivos LAZ")
        
        for i, arquivo_laz in enumerate(arquivos_laz, 1):
            print(f"Processando arquivo {i}/{len(arquivos_laz)}: {arquivo_laz.name}")
            
            pontos, cores = self.processar_arquivo_laz(arquivo_laz)
            
            if pontos is not None and cores is not None:
                todos_pontos.append(pontos)
                todas_cores.append(cores)
        
        if not todos_pontos:
            raise ValueError("Nenhum arquivo LAZ válido foi processado!")
        
        # combina todos os pontos e cores
        pontos_combinados = np.vstack(todos_pontos)
        cores_combinadas = np.vstack(todas_cores)
        
        print(f"Total de pontos carregados: {len(pontos_combinados):,}")
        
        min_coords = np.min(pontos_combinados, axis=0)
        max_coords = np.max(pontos_combinados, axis=0)
        print(f"Bounds ECEF:")
        print(f"  Min: [{min_coords[0]:.2f}, {min_coords[1]:.2f}, {min_coords[2]:.2f}]")
        print(f"  Max: [{max_coords[0]:.2f}, {max_coords[1]:.2f}, {max_coords[2]:.2f}]")
        
        return pontos_combinados, cores_combinadas
    
    def obter_bounds_globais(self, pontos: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return np.min(pontos, axis=0), np.max(pontos, axis=0)
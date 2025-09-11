from pathlib import Path
import numpy as np
import laspy
import json
import shutil
import os
import struct
from py3dtiles.tileset.bounding_volume_box import BoundingVolumeBox

# Configurações
DIRETORIO_EPT = Path("entwine_pointcloud")
DIRETORIO_SAIDA = Path("./3dtiles")
MAXIMO_PONTOS_POR_TILE = 10000
MAX_NIVEIS_OCTREE = 20  # Limite de profundidade da árvore

# Contador global para tiles
tile_counter = 0

def ler_metadados_ept(diretorio_ept: Path) -> dict:
    ept_json_path = diretorio_ept / "ept.json"
    with open(ept_json_path, 'r') as f:
        return json.load(f)

def ler_todos_arquivos_laz(diretorio_ept: Path):
    ept_data_dir = diretorio_ept / "ept-data"
    todos_pontos, todas_cores = [], []
    arquivos_laz = list(ept_data_dir.rglob("*.laz"))

    for arquivo_laz in arquivos_laz:
        try:
            with laspy.open(arquivo_laz) as f:
                las = f.read()
                pontos = np.vstack((las.x, las.y, las.z)).transpose()
                if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
                    cores = np.vstack((las.red, las.green, las.blue)).transpose() // 256
                    cores = cores.astype(np.uint8)
                else:
                    cores = np.full((len(pontos), 3), 255, dtype=np.uint8)
                todos_pontos.append(pontos)
                todas_cores.append(cores)
        except Exception:
            continue
    
    if todos_pontos:
        return np.vstack(todos_pontos), np.vstack(todas_cores)
    raise ValueError("Nenhum arquivo LAZ válido foi encontrado!")

def criar_bounding_volume_from_points(pontos: np.ndarray) -> BoundingVolumeBox:
    min_coords = np.min(pontos, axis=0)
    max_coords = np.max(pontos, axis=0)
    center = (min_coords + max_coords) / 2.0
    half_axes = (max_coords - min_coords) / 2.0
    
    box_array = [
        float(center[0]), float(center[1]), float(center[2]),
        float(half_axes[0]), 0.0, 0.0,
        0.0, float(half_axes[1]), 0.0,
        0.0, 0.0, float(half_axes[2])
    ]
    
    return BoundingVolumeBox.from_list(box_array)

def escrever_tile_pnts(pontos: np.ndarray, cores: np.ndarray, filepath: Path):
    """
    Escreve um arquivo .pnts individual com posições e cores
    """
    # Calcula offsets para posições e cores
    positions_byte_offset = 0
    positions_data = pontos.astype(np.float32).tobytes()
    positions_byte_length = len(positions_data)
    
    colors_byte_offset = positions_byte_length
    colors_data = cores.astype(np.uint8).tobytes()
    colors_byte_length = len(colors_data)
    
    feature_table_json = {
        "POINTS_LENGTH": len(pontos),
        "POSITION": {"byteOffset": positions_byte_offset},
        "RGB": {"byteOffset": colors_byte_offset}
    }
    
    feature_table_str = json.dumps(feature_table_json, separators=(',', ':'))
    feature_table_bytes = feature_table_str.encode('utf-8')
    
    feature_table_len = len(feature_table_bytes)
    padding_length = (8 - (feature_table_len % 8)) % 8
    feature_table_padded = feature_table_bytes + b' ' * padding_length
    
    feature_table_bin_len = positions_byte_length + colors_byte_length
    
    magic = b'pnts'
    version = 1
    byte_length = 28 + len(feature_table_padded) + feature_table_bin_len
    feature_table_json_byte_length = len(feature_table_padded)
    feature_table_binary_byte_length = feature_table_bin_len
    batch_table_json_byte_length = 0
    batch_table_binary_byte_length = 0
    
    header = struct.pack(
        '<4sIIIIII',
        magic,
        version,
        byte_length,
        feature_table_json_byte_length,
        feature_table_binary_byte_length,
        batch_table_json_byte_length,
        batch_table_binary_byte_length
    )

    with open(filepath, "wb") as f:
        f.write(header)
        f.write(feature_table_padded)
        f.write(positions_data)
        f.write(colors_data)

def construir_tiles_octree(pontos: np.ndarray, cores: np.ndarray, nivel: int = 0, bounds=None, output_dir: Path = None) -> dict:
    global tile_counter
    
    if pontos is None or len(pontos) == 0:
        raise ValueError(f"Tentativa de criar tile com 0 pontos no nível {nivel}")
    
    if output_dir is None:
        output_dir = DIRETORIO_SAIDA
        
    if bounds is None:
        min_coords = np.min(pontos, axis=0)
        max_coords = np.max(pontos, axis=0)
        bounds = (min_coords, max_coords)
    else:
        min_coords, max_coords = bounds

    # Criar bounding volume
    bounding_volume = criar_bounding_volume_from_points(pontos)
    
    # Calcular geometric error baseado no tamanho do bounding box
    diagonal = np.linalg.norm(max_coords - min_coords)
    geometric_error = max(1.0, diagonal / (2 ** nivel))

    # Condição de parada - criar tile folha
    if len(pontos) <= MAXIMO_PONTOS_POR_TILE or nivel >= MAX_NIVEIS_OCTREE:
        tile_counter += 1
        filename = f"tile_{tile_counter}.pnts"
        filepath = output_dir / filename
        
        # ESCREVER ARQUIVO .PNTS IMEDIATAMENTE
        escrever_tile_pnts(pontos, cores, filepath)
        
        return {
            "boundingVolume": bounding_volume,
            "geometricError": geometric_error,
            "content": {"uri": filename},
            "refine": "REPLACE"
        }

    # Dividir em octantes
    center = (min_coords + max_coords) / 2.0
    children = []

    for x in [0, 1]:
        for y in [0, 1]:
            for z in [0, 1]:
                min_bound = np.array([
                    min_coords[0] if x == 0 else center[0],
                    min_coords[1] if y == 0 else center[1],
                    min_coords[2] if z == 0 else center[2]
                ])
                max_bound = np.array([
                    center[0] if x == 0 else max_coords[0],
                    center[1] if y == 0 else max_coords[1],
                    center[2] if z == 0 else max_coords[2]
                ])

                mask = (
                    (pontos[:, 0] >= min_bound[0]) & (pontos[:, 0] < max_bound[0]) &
                    (pontos[:, 1] >= min_bound[1]) & (pontos[:, 1] < max_bound[1]) &
                    (pontos[:, 2] >= min_bound[2]) & (pontos[:, 2] < max_bound[2])
                )

                octant_points = pontos[mask]
                octant_colors = cores[mask]

                # Só criar filho se tiver pontos suficientes
                if len(octant_points) > 0:
                    filho = construir_tiles_octree(
                        octant_points,
                        octant_colors,
                        nivel + 1,
                        (min_bound, max_bound),
                        output_dir
                    )
                    children.append(filho)

    # Se não conseguiu criar nenhum filho, tornar este tile uma folha
    if not children:
        tile_counter += 1
        filename = f"tile_{tile_counter}.pnts"
        filepath = output_dir / filename
        
        # ESCREVER ARQUIVO .PNTS IMEDIATAMENTE
        escrever_tile_pnts(pontos, cores, filepath)
        
        return {
            "boundingVolume": bounding_volume,
            "geometricError": geometric_error,
            "content": {"uri": filename},
            "refine": "REPLACE"
        }

    # Tile interno com filhos
    return {
        "boundingVolume": bounding_volume,
        "geometricError": geometric_error,
        "refine": "ADD",
        "children": children
    }

def main():
    global tile_counter
    tile_counter = 0  # Reset do contador
    
    if not DIRETORIO_EPT.exists():
        raise FileNotFoundError(f"Diretório EPT não encontrado: {DIRETORIO_EPT}")

    print("Lendo dados dos arquivos LAZ...")
    todos_pontos, todas_cores = ler_todos_arquivos_laz(DIRETORIO_EPT)
    print(f"Total de pontos carregados: {len(todos_pontos):,}")

    # PASSO 1: Verificação robusta para remover arquivo/diretório existente
    if DIRETORIO_SAIDA.exists():
        print(f"Removendo conteúdo existente: {DIRETORIO_SAIDA}")
        try:
            if DIRETORIO_SAIDA.is_file() or DIRETORIO_SAIDA.is_symlink():
                DIRETORIO_SAIDA.unlink()
                print("  Arquivo removido")
            elif DIRETORIO_SAIDA.is_dir():
                shutil.rmtree(DIRETORIO_SAIDA)
                print("  Diretório removido")
        except Exception as e:
            print(f"  Erro ao remover: {e}")
            raise Exception(f"Não foi possível remover {DIRETORIO_SAIDA}: {e}")
    
    DIRETORIO_SAIDA.mkdir(parents=True, exist_ok=True)

    tile_raiz = construir_tiles_octree(todos_pontos, todas_cores, output_dir=DIRETORIO_SAIDA)

    min_coords = np.min(todos_pontos, axis=0)
    max_coords = np.max(todos_pontos, axis=0)
    diagonal = np.linalg.norm(max_coords - min_coords)
    
    tileset = {
        "asset": {"version": "1.0"},
        "geometricError": diagonal,
        "root": tile_raiz
    }

    tileset_path = DIRETORIO_SAIDA / "tileset.json"
    with open(tileset_path, "w") as f:
        json.dump(tileset, f, indent=2)

if __name__ == "__main__":
    main()

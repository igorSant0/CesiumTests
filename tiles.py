from pathlib import Path
import numpy as np
import laspy
import json
import shutil
from py3dtiles.tileset import TileSet, Tile
from py3dtiles.tileset.content import Pnts, PntsHeader, PntsBody

# Diretório EPT de entrada
DIRETORIO_EPT = Path("entwine_pointcloud")

# Diretório de saída para o tileset gerado
DIRETORIO_SAIDA = Path("./3dtiles_tmp")

# Parâmetros de processamento
MAXIMO_PONTOS_POR_TILE = 10000


def ler_metadados_ept(diretorio_ept):
    ept_json_path = diretorio_ept / "ept.json"
    with open(ept_json_path, 'r') as f:
        metadados = json.load(f)
    return metadados


def ler_todos_arquivos_laz(diretorio_ept):
    ept_data_dir = diretorio_ept / "ept-data"
    todos_pontos = []
    todas_cores = []

    arquivos_laz = list(ept_data_dir.rglob("*.laz"))
    print(f"Encontrados {len(arquivos_laz)} arquivos LAZ para processar...")

    for i, arquivo_laz in enumerate(arquivos_laz):
        print(f"Processando arquivo {i + 1}/{len(arquivos_laz)}: {arquivo_laz.name}")
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
        except Exception as e:
            print(f"Erro ao processar {arquivo_laz}: {e}")
            continue

    if todos_pontos:
        pontos_consolidados = np.vstack(todos_pontos)
        cores_consolidadas = np.vstack(todas_cores)
        return pontos_consolidados, cores_consolidadas
    else:
        raise ValueError("Nenhum arquivo LAZ válido foi encontrado!")


def criar_bounding_volume_from_points(pontos):
    if pontos is None or len(pontos) == 0:
        raise ValueError("Não é possível criar BoundingVolumeBox com 0 pontos.")
    
    min_coords = np.min(pontos, axis=0)
    max_coords = np.max(pontos, axis=0)

    center = (min_coords + max_coords) / 2.0
    half_axes = (max_coords - min_coords) / 2.0

    box_array = [
        float(center[0]), float(center[1]), float(center[2]),  # center
        float(half_axes[0]), 0.0, 0.0,                        # x axis
        0.0, float(half_axes[1]), 0.0,                        # y axis
        0.0, 0.0, float(half_axes[2])                         # z axis
    ]

    # Cria objeto simples para bounding volume
    class SimpleBoundingVolume:
        def __init__(self, box_array):
            self.box = box_array
        def to_dict(self):
            return {"box": self.box}
    return SimpleBoundingVolume(box_array)


def criar_tile_pnts(pontos, cores):
    header = PntsHeader()
    body = PntsBody()
    body.positions = pontos.astype(np.float32).flatten()
    if cores is not None:
        body.colors = cores.astype(np.uint8).flatten()
    return Pnts(header, body)


def dividir_pontos_octree(pontos, cores):
    min_coords = np.min(pontos, axis=0)
    max_coords = np.max(pontos, axis=0)
    centro = (min_coords + max_coords) / 2.0

    sub_regioes = []

    for x_side in [False, True]:
        for y_side in [False, True]:
            for z_side in [False, True]:
                mask = np.ones(len(pontos), dtype=bool)
                mask &= pontos[:, 0] >= centro[0] if x_side else pontos[:, 0] < centro[0]
                mask &= pontos[:, 1] >= centro[1] if y_side else pontos[:, 1] < centro[1]
                mask &= pontos[:, 2] >= centro[2] if z_side else pontos[:, 2] < centro[2]

                if np.any(mask):
                    sub_pontos = pontos[mask]
                    sub_cores = cores[mask]
                    sub_regioes.append((sub_pontos, sub_cores))

    return sub_regioes


def construir_arvore_de_tiles_recursiva(pontos, cores):
    tile = Tile()
    #tile.bounding_volume = criar_bounding_volume_from_points(pontos)

    if len(pontos) <= MAXIMO_PONTOS_POR_TILE:
        tile.content = criar_tile_pnts(pontos, cores)
        return tile
    else:
        tile.children = []
        sub_regioes = dividir_pontos_octree(pontos, cores)
        for sub_pontos, sub_cores in sub_regioes:
            filho = construir_arvore_de_tiles_recursiva(sub_pontos, sub_cores)
            tile.children.append(filho)
        return tile


def main():
    if not DIRETORIO_EPT.exists():
        raise FileNotFoundError(f"Diretório EPT não encontrado: {DIRETORIO_EPT}")

    print("Lendo dados dos arquivos LAZ...")
    todos_pontos, todas_cores = ler_todos_arquivos_laz(DIRETORIO_EPT)
    print(f"Total de pontos carregados: {len(todos_pontos):,}")

    print("Construindo árvore de tiles...")
    tile_raiz = construir_arvore_de_tiles_recursiva(todos_pontos, todas_cores)

    tileset = TileSet(geometric_error=500.0)
    tileset.root = tile_raiz

    # --- Tratamento seguro do diretório de saída ---
    if DIRETORIO_SAIDA.exists():
        print(f"Removendo diretório existente: {DIRETORIO_SAIDA}")
        shutil.rmtree(DIRETORIO_SAIDA)

    print(f"Salvando o tileset em {DIRETORIO_SAIDA}...")
    tileset.write_to_directory(DIRETORIO_SAIDA, overwrite=True)
    print("Conversão concluída com sucesso!")


if __name__ == "__main__":
    main()

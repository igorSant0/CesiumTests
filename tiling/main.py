from pathlib import Path
from lazExtractor import LAZExtractor
from tilesGenerator import TileGenerator

def main():
    DIRETORIO_EPT = Path("../entwine_pointcloud")
    MAXIMO_PONTOS_POR_TILE = 25000
    MAX_NIVEIS_OCTREE = 6
    
    print("Lendo dados dos arquivos LAZ...")
    processor = LAZExtractor(DIRETORIO_EPT)
    todos_pontos, todas_cores = processor.processar_todos_arquivos_laz()
    
    generator = TileGenerator(
        max_points_per_tile=MAXIMO_PONTOS_POR_TILE,
        max_levels=MAX_NIVEIS_OCTREE
    )
    
    tileset = generator.gerar_tileset(todos_pontos, todas_cores)
    generator.salvar_tileset_json(tileset)

if __name__ == "__main__":
    main()
import json
import struct
import numpy as np
import laspy
from pyproj import CRS, Transformer
import os
import glob

class HierarchicalTiler:
    def __init__(self, max_points_per_tile=50000, max_levels=6):
        self.max_points_per_tile = max_points_per_tile
        self.max_levels = max_levels
        self.output_folder = ""
        self.tile_counter = 0
        
    def create_octree_tiles(self, points, colors, bounds, level=0, parent_error=1000.0):
        """
        Cria tiles hierárquicos usando octree para dividir espacialmente os pontos
        """
        current_error = parent_error / 2.0
        
        # Condições para criar tile folha (leaf)
        if len(points) <= self.max_points_per_tile or level >= self.max_levels:
            # Tile folha - criar arquivo .pnts
            tile_name = f"tile_{self.tile_counter}.pnts"
            self.tile_counter += 1
            
            self.write_pnts(points, colors, tile_name)
            
            center = (bounds[0] + bounds[1]) / 2
            size = (bounds[1] - bounds[0]) / 2
            
            return {
                "boundingVolume": {
                    "box": [
                        float(center[0]), float(center[1]), float(center[2]),
                        float(size[0]), 0, 0,
                        0, float(size[1]), 0,
                        0, 0, float(size[2])
                    ]
                },
                "geometricError": max(1.0, current_error),
                "content": {"uri": tile_name},
                "refine": "REPLACE"
            }
        
        # Subdividir em 8 octantes (2x2x2)
        center = (bounds[0] + bounds[1]) / 2
        children = []
        
        for x in [0, 1]:
            for y in [0, 1]:
                for z in [0, 1]:
                    # Definir bounds do octante
                    min_bound = np.array([
                        bounds[0][0] if x == 0 else center[0],
                        bounds[0][1] if y == 0 else center[1],
                        bounds[0][2] if z == 0 else center[2]
                    ])
                    max_bound = np.array([
                        center[0] if x == 0 else bounds[1][0],
                        center[1] if y == 0 else bounds[1][1],
                        center[2] if z == 0 else bounds[1][2]
                    ])
                    
                    # Filtrar pontos neste octante
                    mask = (
                        (points[:, 0] >= min_bound[0]) & (points[:, 0] < max_bound[0]) &
                        (points[:, 1] >= min_bound[1]) & (points[:, 1] < max_bound[1]) &
                        (points[:, 2] >= min_bound[2]) & (points[:, 2] < max_bound[2])
                    )
                    
                    octant_points = points[mask]
                    octant_colors = colors[mask]
                    
                    if len(octant_points) > 0:
                        child_tile = self.create_octree_tiles(
                            octant_points, 
                            octant_colors,
                            (min_bound, max_bound), 
                            level + 1,
                            current_error
                        )
                        children.append(child_tile)
        
        # Se não há filhos, criar tile folha
        if not children:
            tile_name = f"tile_{self.tile_counter}.pnts"
            self.tile_counter += 1
            self.write_pnts(points, colors, tile_name)
            
            center = (bounds[0] + bounds[1]) / 2
            size = (bounds[1] - bounds[0]) / 2
            
            return {
                "boundingVolume": {
                    "box": [
                        float(center[0]), float(center[1]), float(center[2]),
                        float(size[0]), 0, 0,
                        0, float(size[1]), 0,
                        0, 0, float(size[2])
                    ]
                },
                "geometricError": max(1.0, current_error),
                "content": {"uri": tile_name},
                "refine": "REPLACE"
            }
        
        # Tile interno com filhos
        tile_center = (bounds[0] + bounds[1]) / 2
        tile_size = (bounds[1] - bounds[0]) / 2
        
        return {
            "boundingVolume": {
                "box": [
                    float(tile_center[0]), float(tile_center[1]), float(tile_center[2]),
                    float(tile_size[0]), 0, 0,
                    0, float(tile_size[1]), 0,
                    0, 0, float(tile_size[2])
                ]
            },
            "geometricError": current_error,
            "refine": "ADD",
            "children": children
        }
    
    def write_pnts(self, points, colors, filename):
        """
        Escreve um arquivo .pnts individual com posições e cores
        """
        # Calcula offsets para posições e cores
        positions_byte_offset = 0
        positions_data = points.astype(np.float32).tobytes()
        positions_byte_length = len(positions_data)
        
        colors_byte_offset = positions_byte_length
        colors_data = colors.astype(np.uint8).tobytes()
        colors_byte_length = len(colors_data)
        
        feature_table_json = {
            "POINTS_LENGTH": len(points),
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

        with open(f"{self.output_folder}/{filename}", "wb") as f:
            f.write(header)
            f.write(feature_table_padded)
            f.write(positions_data)
            f.write(colors_data)
        
        print(f"  Criado tile: {filename} com {len(points)} pontos e cores")
    
    def create_tileset_json(self, root_tile, output_folder):
        """
        Cria o tileset.json hierárquico
        """
        tileset = {
            "asset": {"version": "1.0"},
            "geometricError": 2000.0,  # Erro geométrico alto para o root
            "root": root_tile
        }

        with open(f"{output_folder}/tileset.json", "w") as f:
            json.dump(tileset, f, indent=2)
        
        print(f"Tileset hierárquico criado com {self.tile_counter} tiles")

def create_tileset(points, output_folder, tile_name="tileset.json"):
    # bounding volume
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    center = (mins + maxs) / 2
    half_size = (maxs - mins) / 2

    tileset = {
        "asset": {"version": "1.0"},
        "geometricError": 500,
        "root": {
            "boundingVolume": {
                "box": [
                    float(center[0]), float(center[1]), float(center[2]),
                    float(half_size[0]), 0, 0,
                    0, float(half_size[1]), 0,
                    0, 0, float(half_size[2])
                ]
            },
            "geometricError": 70,
            "refine": "ADD",
            "content": {"uri": "points.pnts"}
        }
    }

    with open(f"{output_folder}/{tile_name}", "w") as f:
        json.dump(tileset, f, indent=2)


def write_pnts(points, colors, output_file):
    # Calcula offsets para posições e cores
    positions_byte_offset = 0
    positions_data = points.astype(np.float32).tobytes()
    positions_byte_length = len(positions_data)
    
    colors_byte_offset = positions_byte_length
    colors_data = colors.astype(np.uint8).tobytes()
    colors_byte_length = len(colors_data)
    
    # Feature Table JSON
    feature_table_json = {
        "POINTS_LENGTH": len(points),
        "POSITION": {"byteOffset": positions_byte_offset},
        "RGB": {"byteOffset": colors_byte_offset}
    }
    
    feature_table_str = json.dumps(feature_table_json, separators=(',', ':'))
    feature_table_bytes = feature_table_str.encode('utf-8')
    
    # Padding para alinhar a 8 bytes
    feature_table_len = len(feature_table_bytes)
    padding_length = (8 - (feature_table_len % 8)) % 8
    feature_table_padded = feature_table_bytes + b' ' * padding_length
    
    # Feature Table Binary (posições dos pontos + cores)
    feature_table_bin_len = positions_byte_length + colors_byte_length
    
    # Header do arquivo .pnts
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

    with open(output_file, "wb") as f:
        f.write(header)
        f.write(feature_table_padded)
        f.write(positions_data)
        f.write(colors_data)


def extract_colors_from_las(las):
    """
    Extrai informações de cor (RGB) de um arquivo LAS/LAZ
    Retorna array numpy com valores RGB normalizados para 0-255
    """
    try:
        # Verifica se existem dados de cor no arquivo
        if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
            # Alguns arquivos LAS armazenam cores em 16-bit (0-65535)
            # Normaliza para 8-bit (0-255)
            red = las.red
            green = las.green  
            blue = las.blue
            
            # Detecta se está em formato 16-bit ou 8-bit
            max_color = max(red.max(), green.max(), blue.max())
            
            if max_color > 255:
                # Converte de 16-bit para 8-bit
                red = (red / 65535.0 * 255).astype(np.uint8)
                green = (green / 65535.0 * 255).astype(np.uint8)
                blue = (blue / 65535.0 * 255).astype(np.uint8)
            else:
                # Já está em 8-bit
                red = red.astype(np.uint8)
                green = green.astype(np.uint8)
                blue = blue.astype(np.uint8)
            
            # Combina em array RGB
            colors = np.column_stack((red, green, blue))
            print(f"  Cores extraídas: formato {'16-bit' if max_color > 255 else '8-bit'} -> RGB 8-bit")
            return colors
            
        else:
            print("  Aviso: arquivo não contém informações de cor, usando cor padrão (branco)")
            # Retorna cor branca para todos os pontos
            num_points = len(las.points)
            return np.full((num_points, 3), 255, dtype=np.uint8)
            
    except Exception as e:
        print(f"  Erro ao extrair cores: {e}, usando cor padrão (branco)")
        num_points = len(las.points)
        return np.full((num_points, 3), 255, dtype=np.uint8)


def get_epsg_from_las(las):
    """
    Extrai o código EPSG de um arquivo LAS/LAZ, tentando múltiplas fontes
    """
    # Tenta primeiro o método direto
    if hasattr(las.header, 'epsg') and las.header.epsg is not None:
        return las.header.epsg
    
    # Tenta extrair da CRS se disponível
    try:
        if hasattr(las.header, 'crs') and las.header.crs is not None:
            crs = las.header.crs
            if hasattr(crs, 'to_epsg') and crs.to_epsg() is not None:
                return crs.to_epsg()
    except:
        pass
    
    # Para arquivos do Entwine que sabemos ser UTM Zone 22S
    # Baseado na análise do arquivo, sabemos que é EPSG:32722
    print("EPSG não encontrado no header, usando EPSG:32722 (WGS 84 / UTM zone 22S)")
    return 32722


def convert_multiple_laz_to_3dtiles(laz_folder, output_folder, max_points_per_tile=30000):
    """
    Converte múltiplos arquivos LAZ para um tileset 3D Tiles HIERÁRQUICO
    que carrega pontos gradualmente para evitar travamentos
    """
    # Busca todos os arquivos .laz na pasta
    laz_files = glob.glob(os.path.join(laz_folder, "*.laz"))
    
    if not laz_files:
        raise ValueError(f"Nenhum arquivo .laz encontrado na pasta: {laz_folder}")
    
    print(f"Encontrados {len(laz_files)} arquivos .laz")
    print(f"Configuração: máximo {max_points_per_tile} pontos por tile")
    
    all_points = []
    all_colors = []
    epsg_code = None
    transformer = None
    
    for i, laz_file in enumerate(laz_files):
        print(f"Processando arquivo {i+1}/{len(laz_files)}: {os.path.basename(laz_file)}")
        
        try:
            las = laspy.read(laz_file)
            
            # Usa a função melhorada para detectar EPSG
            current_epsg = get_epsg_from_las(las)
            
            # Configura transformação na primeira execução
            if transformer is None:
                epsg_code = current_epsg
                print(f"EPSG detectado/usado: {epsg_code}")
                
                # Configura transformação de coordenadas
                src_crs = CRS.from_epsg(epsg_code)
                dst_crs = CRS.from_epsg(4978)  # ECEF
                transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            
            # Verifica consistência
            elif current_epsg != epsg_code:
                print(f"Aviso: arquivo {os.path.basename(laz_file)} pode ter EPSG diferente ({current_epsg}), usando {epsg_code}")
            
            # Converte pontos para ECEF
            x, y, z = transformer.transform(las.x, las.y, las.z)
            points = np.vstack((x, y, z)).T
            
            # Extrai cores do arquivo
            colors = extract_colors_from_las(las)
            
            all_points.append(points)
            all_colors.append(colors)
            
        except Exception as e:
            print(f"Erro ao processar {os.path.basename(laz_file)}: {e}")
            continue
    
    if not all_points:
        raise ValueError("Nenhum arquivo foi processado com sucesso!")
    
    # Combina todos os pontos e cores
    combined_points = np.vstack(all_points)
    combined_colors = np.vstack(all_colors)
    print(f"Total de pontos combinados: {len(combined_points)} com cores")
    
    # Cria o diretório de saída se não existir
    os.makedirs(output_folder, exist_ok=True)
    
    # NOVA IMPLEMENTAÇÃO: Cria tileset hierárquico
    print("Criando tileset hierárquico para carregamento progressivo...")
    
    tiler = HierarchicalTiler(max_points_per_tile=max_points_per_tile)
    tiler.output_folder = output_folder
    
    # Calcula bounds dos dados
    mins = combined_points.min(axis=0)
    maxs = combined_points.max(axis=0)
    bounds = (mins, maxs)
    
    print(f"Bounds dos dados:")
    print(f"  Min: [{mins[0]:.2f}, {mins[1]:.2f}, {mins[2]:.2f}]")
    print(f"  Max: [{maxs[0]:.2f}, {maxs[1]:.2f}, {maxs[2]:.2f}]")
    
    # Cria estrutura hierárquica
    root_tile = tiler.create_octree_tiles(combined_points, combined_colors, bounds)
    tiler.create_tileset_json(root_tile, output_folder)
    
    print(f"Tileset hierárquico criado com sucesso em: {output_folder}")
    print(f"Agora a nuvem de pontos será carregada progressivamente com cores!")


def convert_multiple_laz_to_3dtiles_legacy(laz_folder, output_folder):
    """
    VERSÃO ANTIGA (mantida para compatibilidade) - cria um único arquivo
    NÃO RECOMENDADA para nuvens grandes pois pode travar o navegador
    """
    # Busca todos os arquivos .laz na pasta
    laz_files = glob.glob(os.path.join(laz_folder, "*.laz"))
    
    if not laz_files:
        raise ValueError(f"Nenhum arquivo .laz encontrado na pasta: {laz_folder}")
    
    print(f"Encontrados {len(laz_files)} arquivos .laz")
    
    all_points = []
    all_colors = []
    epsg_code = None
    transformer = None
    
    for i, laz_file in enumerate(laz_files):
        print(f"Processando arquivo {i+1}/{len(laz_files)}: {os.path.basename(laz_file)}")
        
        try:
            las = laspy.read(laz_file)
            
            # Usa a função melhorada para detectar EPSG
            current_epsg = get_epsg_from_las(las)
            
            # Configura transformação na primeira execução
            if transformer is None:
                epsg_code = current_epsg
                print(f"EPSG detectado/usado: {epsg_code}")
                
                # Configura transformação de coordenadas
                src_crs = CRS.from_epsg(epsg_code)
                dst_crs = CRS.from_epsg(4978)  # ECEF
                transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
            
            # Verifica consistência
            elif current_epsg != epsg_code:
                print(f"Aviso: arquivo {os.path.basename(laz_file)} pode ter EPSG diferente ({current_epsg}), usando {epsg_code}")
            
            # Converte pontos para ECEF
            x, y, z = transformer.transform(las.x, las.y, las.z)
            points = np.vstack((x, y, z)).T
            
            # Extrai cores do arquivo
            colors = extract_colors_from_las(las)
            
            all_points.append(points)
            all_colors.append(colors)
            
        except Exception as e:
            print(f"Erro ao processar {os.path.basename(laz_file)}: {e}")
            continue
    
    if not all_points:
        raise ValueError("Nenhum arquivo foi processado com sucesso!")
    
    # Combina todos os pontos e cores
    combined_points = np.vstack(all_points)
    combined_colors = np.vstack(all_colors)
    print(f"Total de pontos combinados: {len(combined_points)} com cores")
    
    # Cria o diretório de saída se não existir
    os.makedirs(output_folder, exist_ok=True)
    
    # Cria os arquivos finais (versão antiga - um único arquivo)
    write_pnts(combined_points, combined_colors, f"{output_folder}/points.pnts")
    create_tileset(combined_points, output_folder)
    
    print(f"Tileset criado com sucesso em: {output_folder}")


def convert_laz_to_3dtiles(laz_file, output_folder):
    """
    Converte um único arquivo LAZ para 3D Tiles (função original mantida)
    """
    las = laspy.read(laz_file)

    # Usa a função melhorada para detectar EPSG
    epsg_code = get_epsg_from_las(las)
    print(f"EPSG detectado/usado: {epsg_code}")

    src_crs = CRS.from_epsg(epsg_code)
    dst_crs = CRS.from_epsg(4978)  # ECEF
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)

    # converte pontos
    x, y, z = transformer.transform(las.x, las.y, las.z)
    points = np.vstack((x, y, z)).T
    
    # extrai cores
    colors = extract_colors_from_las(las)

    # cria os arquivos
    write_pnts(points, colors, f"{output_folder}/points.pnts")
    create_tileset(points, output_folder)


if __name__ == "__main__":
    # Processa todos os arquivos .laz da pasta entwine_pointcloud/ept-data
    laz_folder = "entwine_pointcloud/ept-data"
    output_folder = "3dTiles"
    
    print("=== CONVERTENDO PARA TILESET HIERÁRQUICO ===")
    print("Isso criará múltiplos arquivos .pnts para carregamento progressivo")
    print("Evitando travamentos do navegador!")
    print()
    
    # Usar a nova função hierárquica com 25.000 pontos por tile
    convert_multiple_laz_to_3dtiles(laz_folder, output_folder, max_points_per_tile=25000)
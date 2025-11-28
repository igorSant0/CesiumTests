#!/bin/sh
set -eu

# Diretório de entrada vindo da env (ou padrão antigo)
INPUT_DIR="${POINTCLOUD_INPUT_DIR:-/PointCloud_pdal_assets/ept-data}"
OUTPUT_DIR="/PointCloud_py3d_assets"

# Verificações básicas
[ -d "$INPUT_DIR" ] || { echo "ERRO: Diretório não existe: $INPUT_DIR" >&2; exit 1; }

# Checa se há pelo menos um .laz (glob não expandido => sem arquivos)
set -- "$INPUT_DIR"/*.laz
if [ "$1" = "$INPUT_DIR/*.laz" ]; then
  echo "ERRO: Nenhum arquivo .laz encontrado em $INPUT_DIR" >&2
  exit 1
fi

echo "Encontrados $# arquivo(s) .laz em $INPUT_DIR"

# Reprojeção
for file in "$@"; do
  pdal translate "$file" "$OUTPUT_DIR/$(basename "$file")" \
    reprojection --filters.reprojection.out_srs=EPSG:4978 --writers.las.compression=true
done

# Verifica se houve saída
set -- "$OUTPUT_DIR"/*.laz
if [ "$1" = "$OUTPUT_DIR/*.laz" ]; then
  echo "ERRO: Nenhum arquivo reprojetado gerado em $OUTPUT_DIR" >&2
  exit 1
fi

py3dtiles convert "$OUTPUT_DIR"/*.laz --out /3dTilesPointCloud --color_scale 256

# Move os tilesets numerados para dentro da pasta points/
mv /3dTilesPointCloud/tileset.*.json /3dTilesPointCloud/points/ 2>/dev/null || true

chmod 777 -R /3dTilesPointCloud
chmod 777 -R /PointCloud_py3d_assets || true
rm -rf /PointCloud_py3d_assets || true
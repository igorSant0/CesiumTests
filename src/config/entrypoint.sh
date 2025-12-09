#!/bin/bash
set -euo pipefail

# Configurações
INPUT_DIR="${POINTCLOUD_INPUT_DIR:-/PointCloud_pdal_assets/ept-data}"
TEMP_DIR="/tmp/processed_laz" 
OUTPUT_DIR="/3dTilesPointCloud"
TILES_SUBFOLDER="$OUTPUT_DIR/tiles_temp"
VOXEL_SIZE="0.05" 

# ------------------------------------------------------------------
# VERIFICAÇÕES DE AMBIENTE
# ------------------------------------------------------------------

echo "--- Verificando Drivers ---"
if pdal --drivers | grep -q "filters.voxeldownsize"; then
    echo "SUCESSO: Driver 'filters.voxeldownsize' encontrado."
else
    echo "ERRO: Driver de downsize não encontrado."
    exit 1
fi

echo "--- Verificando PROJ.db ---"
if [ -f "$PROJ_DATA/proj.db" ]; then
    echo "SUCESSO: proj.db encontrado em $PROJ_DATA"
else
    echo "ERRO: proj.db NÃO encontrado em $PROJ_DATA"
    ls -la /opt/conda/share/proj || true
    exit 1
fi

# ------------------------------------------------------------------
# LIMPEZA
# ------------------------------------------------------------------

echo "Limpando diretórios..."
find "$OUTPUT_DIR" -mindepth 1 -delete 2>/dev/null || true
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Verifica entrada
count=$(ls -1 "$INPUT_DIR"/*.laz 2>/dev/null | wc -l)
if [ "$count" -eq 0 ]; then
    echo "ERRO: Nenhum arquivo .laz encontrado em $INPUT_DIR" >&2
    exit 1
fi

# ------------------------------------------------------------------
# ETAPA 1: OTIMIZAÇÃO (PDAL)
# ------------------------------------------------------------------

echo "--- ETAPA 1: Otimizando e Reprojetando ($count arquivos) ---"

for file in "$INPUT_DIR"/*.laz; do
  filename=$(basename "$file")
  echo "Processando: $filename (Grid: ${VOXEL_SIZE}m)"
  
  pdal translate "$file" "$TEMP_DIR/$filename" \
    reprojection voxeldownsize \
    --filters.reprojection.out_srs=EPSG:4978 \
    --filters.voxeldownsize.cell=$VOXEL_SIZE \
    --writers.las.compression=true
done

# ------------------------------------------------------------------
# ETAPA 2: CONVERSÃO (PY3DTILES)
# ------------------------------------------------------------------

echo "--- ETAPA 2: Gerando 3D Tiles ---"

# --- CORREÇÃO AQUI ---
# Adicionada a flag --color_scale 256 para corrigir o brilho das cores
py3dtiles convert "$TEMP_DIR"/*.laz --out "$TILES_SUBFOLDER" --srs_in 4978 --srs_out 4978 --overwrite --color_scale 256

echo "Organizando arquivos finais..."
cp -r "$TILES_SUBFOLDER"/* "$OUTPUT_DIR/"
rm -rf "$TILES_SUBFOLDER"
rm -rf "$TEMP_DIR"
chmod -R 777 "$OUTPUT_DIR"

echo "Processo concluído com sucesso!"
#!/bin/sh
set -eu

# Reprojeta todos os arquivos para EPSG:4978
for file in /PointCloud_pdal_assets/ept-data/*.laz; do
  pdal translate "$file" "/PointCloud_py3d_assets/$(basename "$file")" \
    reprojection --filters.reprojection.out_srs=EPSG:4978 --writers.las.compression=true
done

py3dtiles convert /PointCloud_py3d_assets/*.laz --out /3dTilesPointCloud --color_scale 256
mv /3dTilesPointCloud/points/tileset*.json /3dTilesPointCloud/
chmod 777 -R /3dTilesPointCloud
chmod 777 -R /PointCloud_pdal_assets
rm -rf /PointCloud_pdal_assets
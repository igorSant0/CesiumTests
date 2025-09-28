#!/bin/sh




#!/bin/sh
set -eu

# Gera os tiles (ajuste o nome do arquivo conforme necessário)
py3dtiles convert /PointCloud_assets/ept-data/*.laz --out /3dTilesPointCloud --srs_in EPSG:32722 --srs_out EPSG:4978 --color_scale 256
mv /3dTilesPointCloud/points/tileset.*.json /3dTilesPointCloud/
chmod 777 -R /3dTilesPointCloud

nginx -g 'daemon off;'
mkdir -p "/usr/share/nginx/html"

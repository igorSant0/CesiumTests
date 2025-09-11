#!/bin/sh




#!/bin/sh
set -eu

log() { printf "%s\n" "$*"; }



log "Copiando resultados para o docroot"
mkdir -p "/usr/share/nginx/html"
rm -rf /usr/share/nginx/html/*
cp -a /app/. /usr/share/nginx/html/
[ -d /assets ] && cp -a /assets/. /usr/share/nginx/html/assets/
[ -d /3dTiles ] && cp -a /3dTiles/. /usr/share/nginx/html/3dTiles/




log "Subindo servidor"

nginx -g 'daemon off;'

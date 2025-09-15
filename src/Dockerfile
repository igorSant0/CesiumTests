FROM nginx:alpine

WORKDIR /app

COPY page/ /usr/share/nginx/html/

COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /3dTiles

EXPOSE 80

FROM nginx:alpine

WORKDIR /app

COPY src/config/nginx.conf /etc/nginx/nginx.conf
COPY src/page/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
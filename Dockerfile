FROM nginx:alpine

# Copia sua aplicação para dentro do Nginx
COPY . /usr/share/nginx/html

# Copia a configuração customizada do Nginx
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

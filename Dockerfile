FROM nginx:alpine

WORKDIR /app

COPY src/config/nginx.conf /etc/nginx/nginx.conf
COPY src/page/ /usr/share/nginx/html/

RUN apk update && \
    apk add --no-cache python3 py3-pip build-base python3-dev g++ openblas-dev && \
    pip3 install --upgrade pip && \
    pip3 install py3dtiles laspy[laszip]

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y nginx llvm-dev build-essential python3-dev g++ libopenblas-dev linux-libc-dev && \
    pip install --upgrade pip && \
    pip install py3dtiles laspy[laszip]

COPY src/config/nginx.conf /etc/nginx/nginx.conf
COPY src/page/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
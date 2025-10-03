FROM pdal/pdal:latest

RUN apt-get update && \
    apt-get install -y python3 python3-pip nginx && \
    pip3 install --upgrade pip && \
    pip3 install py3dtiles laspy[laszip]

WORKDIR /app

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh



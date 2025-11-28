FROM pdal/pdal:latest

RUN conda install -n pdal python=3.13 -y && \
    apt-get update && \
    apt-get install -y build-essential nginx && \
    conda run -n pdal pip install --upgrade pip && \
    conda run -n pdal pip install py3dtiles laspy[laszip]

WORKDIR /app

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

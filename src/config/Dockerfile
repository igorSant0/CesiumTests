FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y nginx && \
    pip install --upgrade pip && pip install --upgrade py3dtiles laspy[laszip]

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
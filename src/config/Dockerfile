FROM continuumio/miniconda3:latest

SHELL ["/bin/bash", "-c"]

WORKDIR /app

# Instala dependências, incluindo dos2unix para corrigir scripts do Windows
RUN apt-get update && \
    apt-get install -y build-essential nginx git dos2unix && \
    rm -rf /var/lib/apt/lists/*

# Instala PDAL, PROJ e dependências Python
RUN conda config --add channels conda-forge && \
    conda config --set channel_priority strict && \
    conda install -y python=3.10 pdal python-pdal laspy numpy proj-data && \
    pip install --upgrade pip && \
    pip install py3dtiles

# Variáveis de ambiente CRÍTICAS para o PDAL encontrar o proj.db
ENV PROJ_LIB=/opt/conda/share/proj
ENV PROJ_DATA=/opt/conda/share/proj

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh

# AQUI ESTÁ A CORREÇÃO DE SEGURANÇA:
# 1. Converte quebras de linha Windows -> Unix (evita exec format error)
# 2. Torna executável
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
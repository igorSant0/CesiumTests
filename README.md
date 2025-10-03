# CesiumJS Viewer com Docker

Este repositório contém um ambiente de testes para visualização de nuvens de pontos utilizando **CesiumJS**, com suporte a dados em formato **EPT (Entwine Point Tile)**.

---

## 🚀 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 📂 Organização dos dados

ASSETS_PATH=/home/ralph/Documentos/agrosmart/media/orthomosaic/0/0/0/assets/entwine_pointcloud
TILES_PATH=/home/ralph/Documentos/agrosmart/media/orthomosaic/0/0/0/assets/3dTiles

`/home/ralph/Documentos/agrosmart/media/orthomosaic/0/0/0/assets` é a pasta do agrosmart onde estão os assets, é só jogar a `entwine_pointcloud` na env do `ASSETS_PATH` que vai dar certo
o `TILES_PATH` tb mapeei para o hot para permanencia. se não houver, ele cria automaticamente.

MAS são 2 serviços no compose, cada um com uma funcionalidade. 1 pra buildar os tiles, outro para servir

---

## ▶️ Como rodar

para buildar os tiles do assets escolhido execute
(só precisa rodar esse 1x)
`docker compose -f docker-compose.build_tiles.yml up --build`

e depois para servir, só executar `docker compose up --build`

A aplicação ficará disponível em:

👉 [http://localhost:8989/app](http://localhost:8989/app)

---

## 🌐 Porta de Visualização

A aplicação é servida via **porta 8000**.

---

## 📝 Observações

- O container já expõe a pasta do projeto local para dentro do ambiente do Docker.
- Sempre que fizer alterações em `index.html`, `style.css` ou `script.js`, basta atualizar a página no navegador.
- Caso não veja a mudança, faça um **hard reload** (`Ctrl + Shift + R` ou `Ctrl + F5`).

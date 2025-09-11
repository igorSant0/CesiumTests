# CesiumJS Viewer com Docker

Este repositório contém um ambiente de testes para visualização de nuvens de pontos utilizando **CesiumJS**, com suporte a dados em formato **EPT (Entwine Point Tile)**.

---

## 🚀 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

Além disso, o ambiente utiliza as seguintes bibliotecas Python (caso queira rodar localmente sem Docker):

- [py3dtiles](https://github.com/Oslandia/py3dtiles)
- [laszip](https://laszip.org/)
- [laspy](https://github.com/laspy/laspy)
- [pyproj](https://pyproj4.github.io/pyproj/stable/)
- [numpy](https://numpy.org/)

---

## 📂 Organização dos dados

Após clonar este repositório, é necessário **copiar manualmente** a pasta `entwine_pointcloud` para dentro da pasta clonada.

O caminho de origem dos dados deve ser algo como:

```
media/orthomosaic/0/0/0/assets/entwine_pointcloud
```

E o conteúdo mínimo esperado dentro da pasta é:

```
entwine_pointcloud/
├── ept-data/
└── ept.json
```

---

## ▶️ Como rodar

Caso a instalação das bibliotecas não funcione, você pode criar um ambiente virtual e instalar manualmente com:

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate    # Windows

pip install py3dtiles laszip laspy pyproj numpy
```

Em seguida, entre na pasta `tiling`:

```bash
cd tiling
```

E rode o script para gerar o dataset **3D Tiles**:

```bash
python main.py
```

Com o dataset criado, suba o container com:

```bash
docker-compose up --build
```

A aplicação ficará disponível em:

👉 [http://localhost:8080/page](http://localhost:8080/page)

---

## 🌐 Porta de Visualização

A aplicação é servida via **porta 8080**.

---

## 📝 Observações

- O container já expõe a pasta do projeto local para dentro do ambiente do Docker.  
- Sempre que fizer alterações em `index.html`, `style.css` ou `script.js`, basta atualizar a página no navegador.  
- Caso não veja a mudança, faça um **hard reload** (`Ctrl + Shift + R` ou `Ctrl + F5`).  


- O container já expõe a pasta do projeto local para dentro do ambiente do Docker.  
- Sempre que fizer alterações em `index.html`, `style.css` ou `script.js`, basta atualizar a página no navegador.  
- Caso não veja a mudança, faça um **hard reload** (`Ctrl + Shift + R` ou `Ctrl + F5`).  

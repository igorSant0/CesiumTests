// Configuração inicial do Cesium
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5M2M3MTk2MC1jY2JhLTRkNmYtYmNlZC03NzRjNTIxNmMxMmEiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NTY4MTc4MTJ9.anLO7mF-4WBQt_M1t6w97sTS10Cl1zmRi6_4zQyj2rw';

Cesium.RequestScheduler.maximumRequestsPerServer = 8; // Reduzido para evitar sobrecarga

const viewer = new Cesium.Viewer('cesiumContainer', {
    terrain: Cesium.Terrain.fromWorldTerrain(),
    homeButton: true,
    sceneModePicker: true,
    baseLayerPicker: true,
    navigationHelpButton: true,
    animation: false,
    timeline: false,
    fullscreenButton: true,
    vrButton: false
});

viewer.scene.globe.enableLighting = true;
viewer.scene.fog.enabled = true;
viewer.scene.skyAtmosphere.show = true;
viewer.scene.sun.show = true;

let loadedTileset = null;

async function carregarModeloTexturizado() {
    try {
        console.log("Carregando tileset 3D texturizado...");
        
        const tileset = await Cesium.Cesium3DTileset.fromUrl(
            "http://localhost:8000/3dTilesTexturing/tileset.json",
            {
                maximumScreenSpaceError: 16, // Aumentado para melhor performance
                skipLevelOfDetail: false,
                baseScreenSpaceError: 1024,
                skipScreenSpaceErrorFactor: 16,
                skipLevels: 0,
                immediatelyLoadDesiredLevelOfDetail: false, // Permitir carregamento progressivo
                loadSiblings: false, // Reduzir carga de rede
                cullWithChildrenBounds: false, // Manter desabilitado
                cullRequestsWhileMoving: false, // Manter desabilitado
                dynamicScreenSpaceError: true, // Habilitar para melhor adaptação
                maximumMemoryUsage: 2048, // Mais memória para manter tiles
                preloadWhenHidden: false, // Reduzir uso desnecessário
                preloadFlightDestinations: false,
                progressiveResolutionHeightFraction: 0.3,
                preferLeaves: false // Permitir carregamento hierárquico
            }
        );

        viewer.scene.primitives.add(tileset);
        console.log("Tileset 3D carregado e adicionado à cena!");

        tileset.tileFailed.addEventListener(function (error) {
            console.error("Falha ao carregar tile:", error);
        });
        
        tileset.allTilesLoaded.addEventListener(function () {
            console.log("Todos os tiles carregados!");
        });

        tileset.tileUnload.addEventListener(function(tile) {
            console.log("Tile descarregado:", tile.contentUri || "tile sem URI");
        });

        // Forçar carregamento de todos os tiles LOD-0 (máxima qualidade)
        tileset.tileLoad.addEventListener(function(tile) {
            console.log("Tile carregado:", tile.contentUri || "tile sem URI");
        });

        await tileset.readyPromise;
        console.log("Tileset pronto!");
        
        console.log("Bounding sphere:", tileset.boundingSphere);
        console.log("Tileset show:", tileset.show);
        console.log("Root tile:", tileset.root);

        const longitude = -49.19246541;
        const latitude = -20.57063518;
        const altitude = 432.12;
        
        console.log("Usando transformação original do tileset gerado pelo Obj2Tiles");

        try {
            await viewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, altitude + 100), // Altura moderada
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-45), // Ângulo melhor para visualização
                    roll: 0.0
                }
            });
            console.log(`Câmera posicionada manualmente em: ${latitude}, ${longitude}, ${altitude + 100}m`);
        } catch (error) {
            console.warn("Erro ao posicionar câmera manualmente, usando zoomTo:", error);
            await viewer.zoomTo(tileset);
            console.log("Usado zoomTo para posicionar câmera automaticamente");
        }
        
        loadedTileset = tileset;
        
        return tileset;

    } catch (error) {
        console.error("Erro ao carregar tileset 3D:", error);
        alert("Erro ao carregar modelo texturizado. Verifique se o tileset foi gerado corretamente.");
        throw error;
    }
}

function adicionarControles() {
    const toolbar = document.createElement('div');
    toolbar.className = 'cesium-button-toolbar';
    toolbar.style.position = 'absolute';
    toolbar.style.top = '10px';
    toolbar.style.left = '10px';
    toolbar.style.background = 'rgba(42, 42, 42, 0.8)';
    toolbar.style.padding = '10px';
    toolbar.style.borderRadius = '5px';

    const reloadButton = document.createElement('button');
    reloadButton.textContent = 'Recarregar Tileset';
    reloadButton.className = 'cesium-button';
    reloadButton.onclick = () => {
        viewer.scene.primitives.removeAll();
        carregarModeloTexturizado();
    };

    const resetCameraButton = document.createElement('button');
    resetCameraButton.textContent = 'Resetar Câmera';
    resetCameraButton.className = 'cesium-button';
    resetCameraButton.onclick = () => {
        const longitude = -49.19246541;
        const latitude = -20.57063518;
        const altitude = 432.12;
        
        viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, altitude + 500),
            orientation: {
                heading: 0,
                pitch: Cesium.Math.toRadians(-45),
                roll: 0
            }
        });
    };

    toolbar.appendChild(reloadButton);
    toolbar.appendChild(resetCameraButton);
    document.body.appendChild(toolbar);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Inicializando visualizador de modelo texturizado...");
    
    adicionarControles();
    
    carregarModeloTexturizado();
});

window.addEventListener('error', (e) => {
    console.error('Erro global:', e.error);
});
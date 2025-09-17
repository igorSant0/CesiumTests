// Configuração inicial do Cesium
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5M2M3MTk2MC1jY2JhLTRkNmYtYmNlZC03NzRjNTIxNmMxMmEiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NTY4MTc4MTJ9.anLO7mF-4WBQt_M1t6w97sTS10Cl1zmRi6_4zQyj2rw';

// Configurações de performance para modelos locais
Cesium.RequestScheduler.maximumRequestsPerServer = 8;

// Inicializar viewer
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

// Função para carregar modelo texturizado
async function carregarModeloTexturizado() {
    try {
        console.log("Carregando modelo texturizado...");
        
        // Carregando modelo GLB como Entity
        const entity = viewer.entities.add({
            name: "Modelo 3D Texturizado",
            position: Cesium.Cartesian3.fromDegrees(-47.8825, -15.7975, 100), // Brasília
            model: {
                uri: "http://localhost:8000/odm_texturing/odm_textured_model_geo.glb",
                scale: 1.0,
                minimumPixelSize: 64,
                maximumScale: 20000,
                color: Cesium.Color.WHITE,
                colorBlendMode: Cesium.ColorBlendMode.MIX,
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                silhouetteColor: Cesium.Color.YELLOW,
                silhouetteSize: 2,
                runAnimations: false,
                allowPicking: true
            }
        });

        // Aguardar o modelo carregar
        await entity.model.readyPromise;
        console.log("Modelo texturizado carregado com sucesso!");

        // Centralizar na visualização
        viewer.trackedEntity = entity;

        // Ajustar câmera para melhor visualização
        viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(-47.8825, -15.7975, 500),
            orientation: {
                heading: Cesium.Math.toRadians(0),
                pitch: Cesium.Math.toRadians(-45),
                roll: 0.0
            }
        });

        return entity;

    } catch (error) {
        console.error("Erro ao carregar modelo texturizado:", error);
        
        // Tentar carregar sem extensão (caso seja formato diferente)
        try {
            console.log("Tentando carregar sem extensão .glb...");
            
            const entity = viewer.entities.add({
                name: "Modelo 3D Texturizado (alt)",
                position: Cesium.Cartesian3.fromDegrees(-47.8825, -15.7975, 100),
                model: {
                    uri: "http://localhost:8000/odm_texturing/odm_textured_model_geo",
                    scale: 1.0,
                    minimumPixelSize: 64,
                    maximumScale: 20000,
                    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                }
            });

            viewer.trackedEntity = entity;
            return entity;

        } catch (secondError) {
            console.error("Erro ao carregar modelo (segunda tentativa):", secondError);
            alert("Erro ao carregar modelo texturizado. Verifique se o arquivo existe em: http://localhost:8000/odm_texturing/");
        }
    }
}

// Adicionar controles de interface
function adicionarControles() {
    // Painel de controles
    const toolbar = document.createElement('div');
    toolbar.className = 'cesium-button-toolbar';
    toolbar.style.position = 'absolute';
    toolbar.style.top = '10px';
    toolbar.style.left = '10px';
    toolbar.style.background = 'rgba(42, 42, 42, 0.8)';
    toolbar.style.padding = '10px';
    toolbar.style.borderRadius = '5px';

    // Botão para recarregar modelo
    const reloadButton = document.createElement('button');
    reloadButton.textContent = 'Recarregar Modelo';
    reloadButton.className = 'cesium-button';
    reloadButton.onclick = () => {
        viewer.entities.removeAll();
        carregarModeloTexturizado();
    };

    // Botão para resetar câmera
    const resetCameraButton = document.createElement('button');
    resetCameraButton.textContent = 'Resetar Câmera';
    resetCameraButton.className = 'cesium-button';
    resetCameraButton.onclick = () => {
        viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(-47.8825, -15.7975, 500),
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

// Inicializar aplicação
document.addEventListener('DOMContentLoaded', () => {
    console.log("Inicializando visualizador de modelo texturizado...");
    
    // Adicionar controles
    adicionarControles();
    
    // Carregar modelo
    carregarModeloTexturizado();
});

// Tratamento de erros globais
window.addEventListener('error', (e) => {
    console.error('Erro global:', e.error);
});
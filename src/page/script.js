Cesium.RequestScheduler.maximumRequestsPerServer = 8;
Cesium.RequestScheduler.throttleRequests = true;

const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI0ZjM0MjE0Yi03OTRjLTRmMGMtOWVmZS1mMGE5YTg0MTkxZDYiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NjQzMzg1NDV9.8eFlv1nIAVwIpwakTuuDBdd9nQYlkedHyCAfpyN3heM";

Cesium.Ion.defaultAccessToken = token;

const viewer = new Cesium.Viewer("cesiumContainer", {
    // --- Remoção de Widgets (Botões e Interface) ---
    baseLayerPicker: false,
    terrain: Cesium.Terrain.fromWorldTerrain(),
    geocoder: false,
    homeButton: false,           // Remove o botão da "Casinha"
    infoBox: false,
    navigationHelpButton: false, // Remove o botão de Ajuda "?"
    sceneModePicker: false,
    timeline: false,             // Remove a linha do tempo
    animation: false,            // Remove o relógio
    vrButton: false,
    fullscreenButton: false,
    selectionIndicator: false,   // Remove o quadrado verde de seleção
    
    // Configurações de renderização
    requestRenderMode: false,
    maximumRenderTimeChange: Infinity,
});

// --- REMOVE O LOGO DA CESIUM E CRÉDITOS ---
// Esta linha oculta a barra inferior com o PNG do Cesium e atribuições
viewer.cesiumWidget.creditContainer.style.display = "none";

// Configurações Globais da Cena
viewer.scene.globe.enableLighting = false;
viewer.scene.fog.enabled = false;
viewer.scene.skyAtmosphere.show = false;
viewer.scene.sun.show = false;
viewer.scene.moon.show = false;
viewer.scene.skyBox.show = false;
viewer.scene.globe.show = true;
viewer.scene.globe.depthTestAgainstTerrain = false;

// Opções de carregamento inicial
const options = {
    maximumScreenSpaceError: 48,
    maximumMemoryUsage: 2048,
    skipLevelOfDetail: false,
    preferLeaves: false,
};

async function carregarTileset() {
    try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl(
            "http://localhost:8000/3dTilesPointCloud/tileset.json",
            options
        );

        viewer.scene.primitives.add(tileset);

        // --- Configurações Estáticas ---
        
        // LOD
        tileset.maximumScreenSpaceError = 48;

        // Tamanho do Ponto
        tileset.pointCloudShading.pointSize = 12;

        // Eye Dome Lighting (EDL)
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = 0.8;
        tileset.pointCloudShading.eyeDomeLightingRadius = 1.5;

        // Atenuação
        tileset.pointCloudShading.attenuation = true;
        tileset.pointCloudShading.maximumAttenuation = 4;

        // Ajuste da Câmera
        viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-35), 500));

        // Pós-processamento
        viewer.scene.postProcessStages.fxaa.enabled = true;

    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset();
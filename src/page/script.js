Cesium.RequestScheduler.maximumRequestsPerServer = 8;
Cesium.RequestScheduler.throttleRequests = true;

const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5M2M3MTk2MC1jY2JhLTRkNmYtYmNlZC03NzRjNTIxNmMxMmEiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NTY4MTc4MTJ9.anLO7mF-4WBQt_M1t6w97sTS10Cl1zmRi6_4zQyj2rw";

const viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayerPicker: false,
    terrain: Cesium.Terrain.fromWorldTerrain(),
    geocoder: false,
    homeButton: true,
    infoBox: false,
    navigationHelpButton: true,
    sceneModePicker: false,
    timeline: false,
    animation: true,
    vrButton: false,
    fullscreenButton: false,
    requestRenderMode: true,
    maximumRenderTimeChange: Infinity,
});

viewer.scene.globe.enableLighting = false;
viewer.scene.fog.enabled = false;
viewer.scene.skyAtmosphere.show = false;
viewer.scene.sun.show = false;
viewer.scene.moon.show = false;
viewer.scene.skyBox.show = false;

const options = {
    maximumScreenSpaceError: 8,        // menor valor = mais detalhes
    maximumMemoryUsage: 2048,          // mais ram
    dynamicScreenSpaceError: true,     // ajusta detalhes conforme zoom
    dynamicScreenSpaceErrorDensity: 0.002, // densidade para ajuste dinâmico
    dynamicScreenSpaceErrorFactor: 4.0,    // fator para ajuste dinâmico
    dynamicScreenSpaceErrorHeightFalloff: 0.25, // suaviza transição de detalhes
    skipLevelOfDetail: false,          // carrega todos os níveis de detalhe
    baseScreenSpaceError: 1024,        // erro base para tiles
    preloadWhenHidden: false,           // precarrega tiles fora de vista
    preloadFlightDestinations: true,   // precarrega tiles durante animações
    preferLeaves: true,                // prefere tiles folha para mais detalhes
    loadSiblings: true,                // carrega tiles irmãos juntos
    cullWithChildrenBounds: true,      // culling mais eficiente
    cullRequestsWhileMoving: false,    // não cancela requests durante movimento
    foveatedScreenSpaceError: true,    // ajusta detalhes conforme foco
    foveatedConeSize: 0.1,             // tamanho do cone de foco
    foveatedMinimumScreenSpaceErrorRelaxation: 0.0, // relaxamento mínimo
    foveatedInterpolationCallback: undefined,       // callback customizado
    foveatedTimeDelay: 0.2,            // delay para ajuste de foco
}

async function carregarTileset() {
    try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl("http://localhost:8000/3dTilesPointCloud/tileset.json", options);

        viewer.scene.primitives.add(tileset);

        tileset.pointCloudShading.pointSize = 6.0; // valores entre 2 e 8 para melhor qualidade
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = 0.8;
        tileset.pointCloudShading.eyeDomeLightingRadius = 1.5;

        viewer.zoomTo(tileset);
        viewer.scene.postProcessStages.fxaa.enabled = true;

        tileset.tileFailed.addEventListener(function (error) {
            console.error("Falha ao carregar tile:", error);
        });

    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset()
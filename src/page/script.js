Cesium.RequestScheduler.maximumRequestsPerServer = 12;
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
    animation: false,
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

async function carregarTileset() {
    try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl("http://localhost:8000/3dTilesPointCloud/tileset.json", {
            maximumScreenSpaceError: 48,
            maximumMemoryUsage: 1024,
        });

        viewer.scene.primitives.add(tileset);

        tileset.pointCloudShading.pointSize = 12.0;
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
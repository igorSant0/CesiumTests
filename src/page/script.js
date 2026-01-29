Cesium.RequestScheduler.maximumRequestsPerServer = 8;
Cesium.RequestScheduler.throttleRequests = true;

const token =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI0ZjM0MjE0Yi03OTRjLTRmMGMtOWVmZS1mMGE5YTg0MTkxZDYiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NjQzMzg1NDV9.8eFlv1nIAVwIpwakTuuDBdd9nQYlkedHyCAfpyN3heM";

Cesium.Ion.defaultAccessToken = token;
const viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayerPicker: false,
    terrain: Cesium.Terrain.fromWorldTerrain(),
    geocoder: false,
    homeButton: false,
    infoBox: false,
    navigationHelpButton: false,
    sceneModePicker: false,
    timeline: false,
    animation: false,
    vrButton: false,
    fullscreenButton: false,
    requestRenderMode: false,
    maximumRenderTimeChange: Infinity,
    navigationInstructionsInitiallyVisible: false,
    creditContainer: undefined,
    selectionIndicator: false,
    baseLayerPicker: false,
    navigationHelpButton: false,
    infoBox: false,
    homeButton: false,
    sceneModePicker: false,
    timeline: false,
    animation: false,
    vrButton: false,
    fullscreenButton: false,
});

viewer.scene.globe.enableLighting = false;
viewer.scene.fog.enabled = false;
viewer.scene.skyAtmosphere.show = false;
viewer.scene.sun.show = false;
viewer.scene.moon.show = false;
viewer.scene.skyBox.show = false;
viewer.scene.globe.show = true;
viewer.scene.globe.depthTestAgainstTerrain = false;

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

        tileset.maximumScreenSpaceError = 48;
        tileset.pointCloudShading.pointSize = 3;
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = 0.8;
        tileset.pointCloudShading.eyeDomeLightingRadius = 1.5;
        tileset.pointCloudShading.attenuation = true;
        tileset.pointCloudShading.maximumAttenuation = 4;

        viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-35), 500));
        viewer.scene.postProcessStages.fxaa.enabled = true;
    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset();

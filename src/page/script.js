Cesium.RequestScheduler.maximumRequestsPerServer = 6;
Cesium.RequestScheduler.throttleRequests = true;
// token de uso global
const token =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5M2M3MTk2MC1jY2JhLTRkNmYtYmNlZC03NzRjNTIxNmMxMmEiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NTY4MTc4MTJ9.anLO7mF-4WBQt_M1t6w97sTS10Cl1zmRi6_4zQyj2rw";

const viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayerPicker: false,
    terrain: Cesium.Terrain.fromWorldTerrain(),
    geocoder: false,
    homeButton: false,
    infoBox: true,
    navigationHelpButton: false,
    sceneModePicker: false,
    timeline: false,
    animation: false,
    vrButton: false,
    fullscreenButton: false,
    requestRenderMode: true, // Renderizar apenas quando necessário
    maximumRenderTimeChange: Infinity,
});

// configurações de performance
viewer.scene.globe.enableLighting = false;
viewer.scene.fog.enabled = false;
viewer.scene.skyAtmosphere.show = false;
viewer.scene.sun.show = false;
viewer.scene.moon.show = false;
viewer.scene.skyBox.show = false;

let loadedTileset = null;
let nuvemCentro = null;

console.log("Iniciando carregamento do tileset...");

async function carregarTileset() {
    try {
        const tilesetOptions = {
            url: "http://localhost:8000/3dTiles/tileset.json",
            debugShowBoundingVolume: false,
            debugShowContentBoundingVolume: false,
            maximumScreenSpaceError: 64,
            preloadWhenHidden: false,
            preloadFlightDestinations: false,
            skipLevelOfDetail: true,
            baseScreenSpaceError: 1024,
            skipScreenSpaceErrorFactor: 16,
            skipLevels: 1,
            immediatelyLoadDesiredLevelOfDetail: false,
            loadSiblings: true,
            cullWithChildrenBounds: true,
            cullRequestsWhileMoving: true,
            cullRequestsWhileMovingMultiplier: 60.0,
            dynamicScreenSpaceError: true,
            dynamicScreenSpaceErrorDensity: 0.00278,
            dynamicScreenSpaceErrorFactor: 4.0,
            dynamicScreenSpaceErrorHeightFalloff: 0.25,
            maximumMemoryUsage: 512,
        };

        // carregando o datasaet
        const tileset = await Cesium.Cesium3DTileset.fromUrl("http://localhost:8000/3dTiles/tileset.json");

        viewer.scene.primitives.add(tileset);
        console.log("Tileset carregado e adicionado à cena com sucesso!");

        tileset.tileFailed.addEventListener(function (error) {
            console.error("Falha ao carregar tile:", error);
        });
        tileset.allTilesLoaded.addEventListener(function () {
            console.log("Todos os tiles visíveis foram carregados!");
        });

        console.log("Bounding sphere:", tileset.boundingSphere);

        tileset.pointCloudShading.pointSize = 15.0;
        tileset.pointCloudShading.maximumAttenuation = 0;
        tileset.pointCloudShading.baseResolution = 0;
        tileset.pointCloudShading.geometricErrorScale = 1.0;
        tileset.pointCloudShading.eyeDomeLighting = false;
        tileset.pointCloudShading.eyeDomeLightingStrength = 1.0;
        tileset.pointCloudShading.eyeDomeLightingRadius = 1.0;
        tileset.pointCloudShading.attenuation = false;
        console.log("Configurações de point cloud aplicadas");

        loadedTileset = tileset;

        const center = tileset.boundingSphere.center;
        const carto = Cesium.Cartographic.fromCartesian(center);
        const lon = Cesium.Math.toDegrees(carto.longitude);
        const lat = Cesium.Math.toDegrees(carto.latitude);
        const height = carto.height;
        nuvemCentro = { lon, lat, height };
        console.log("Centro da nuvem:", `Lon: ${lon.toFixed(6)}, Lat: ${lat.toFixed(6)}, Alt: ${height.toFixed(2)}m`);

        viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0.0, -0.5, 300));
        console.log("Zoom inicial aplicado.");
    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset();

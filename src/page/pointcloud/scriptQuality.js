//ip: 192.168.0.103
Cesium.RequestScheduler.maximumRequestsPerServer = 12;
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
    requestRenderMode: true,
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
            maximumScreenSpaceError: 48,
            preloadWhenHidden: false,
            preloadFlightDestinations: false,
            skipLevelOfDetail: false,
            baseScreenSpaceError: 768,
            skipScreenSpaceErrorFactor: 12,
            skipLevels: 0,
            immediatelyLoadDesiredLevelOfDetail: false,
            loadSiblings: true,
            cullWithChildrenBounds: true,
            cullRequestsWhileMoving: true,
            cullRequestsWhileMovingMultiplier: 60.0,
            dynamicScreenSpaceError: true,
            dynamicScreenSpaceErrorDensity: 0.00278,
            dynamicScreenSpaceErrorFactor: 3.0,
            dynamicScreenSpaceErrorHeightFalloff: 0.15,
            maximumMemoryUsage: 1024,
        };

        // carregando o datasaet
        const tileset = await Cesium.Cesium3DTileset.fromUrl("http://localhost:8000/3dTiles/tileset.json", tilesetOptions);

        viewer.scene.primitives.add(tileset);
        console.log("Tileset carregado e adicionado à cena com sucesso!");

        tileset.tileFailed.addEventListener(function (error) {
            console.error("Falha ao carregar tile:", error);
        });
        tileset.allTilesLoaded.addEventListener(function () {
            console.log("Todos os tiles visíveis foram carregados!");
        });

        console.log("Bounding sphere:", tileset.boundingSphere);

        tileset.pointCloudShading.pointSize = 12.0;
        tileset.pointCloudShading.maximumAttenuation = 4;
        tileset.pointCloudShading.baseResolution = 0;
        tileset.pointCloudShading.geometricErrorScale = 1.0;
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = 0.8;
        tileset.pointCloudShading.eyeDomeLightingRadius = 1.5;
        tileset.pointCloudShading.attenuation = true;
        tileset.pointCloudShading.attenuationRange = 800;
        console.log("Configurações de point cloud aplicadas");

        loadedTileset = tileset;

        const center = tileset.boundingSphere.center;
        const carto = Cesium.Cartographic.fromCartesian(center);
        const lon = Cesium.Math.toDegrees(carto.longitude);
        const lat = Cesium.Math.toDegrees(carto.latitude);
        const height = carto.height;
        nuvemCentro = { lon, lat, height };
        console.log("Centro da nuvem:", `Lon: ${lon.toFixed(6)}, Lat: ${lat.toFixed(6)}, Alt: ${height.toFixed(2)}m`);

        viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0.0, -0.5, 200));
        console.log("Zoom inicial aplicado.");

        viewer.scene.postProcessStages.fxaa.enabled = true;

        // Conectar controles da UI
        document.getElementById("lod").addEventListener("input", (event) => {
            const value = parseInt(event.target.value);
            loadedTileset.maximumScreenSpaceError = value;
            document.getElementById("lodValue").innerText = value;
            viewer.scene.requestRender();
        });

        document.getElementById("pointSize").addEventListener("input", (event) => {
            const value = parseInt(event.target.value);
            loadedTileset.pointCloudShading.pointSize = value;
            document.getElementById("pointSizeValue").innerText = value;
            viewer.scene.requestRender();
        });

        document.getElementById("edlStrength").addEventListener("input", (event) => {
            const value = parseFloat(event.target.value);
            loadedTileset.pointCloudShading.eyeDomeLightingStrength = value;
            document.getElementById("edlStrengthValue").innerText = value;
            viewer.scene.requestRender();
        });

        document.getElementById("edlRadius").addEventListener("input", (event) => {
            const value = parseFloat(event.target.value);
            loadedTileset.pointCloudShading.eyeDomeLightingRadius = value;
            document.getElementById("edlRadiusValue").innerText = value;
            viewer.scene.requestRender();
        });

        document.getElementById("maxAttenuation").addEventListener("input", (event) => {
            const value = parseInt(event.target.value);
            loadedTileset.pointCloudShading.maximumAttenuation = value;
            document.getElementById("maxAttenuationValue").innerText = value;
            viewer.scene.requestRender();
        });

        document.getElementById("toggleEDL").addEventListener("click", () => {
            loadedTileset.pointCloudShading.eyeDomeLighting = !loadedTileset.pointCloudShading.eyeDomeLighting;
            viewer.scene.requestRender();
        });


    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}
carregarTileset();
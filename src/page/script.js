Cesium.RequestScheduler.maximumRequestsPerServer = 8;
Cesium.RequestScheduler.throttleRequests = true;

const token =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI0ZjM0MjE0Yi03OTRjLTRmMGMtOWVmZS1mMGE5YTg0MTkxZDYiLCJpZCI6MzM3MjMwLCJpYXQiOjE3NjQzMzg1NDV9.8eFlv1nIAVwIpwakTuuDBdd9nQYlkedHyCAfpyN3heM";

Cesium.Ion.defaultAccessToken = token;
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
    requestRenderMode: false,
    maximumRenderTimeChange: Infinity,
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

        // Configurações Iniciais e Sincronização dos Sliders
        tileset.maximumScreenSpaceError = Number(document.getElementById("lod").value);
        tileset.pointCloudShading.pointSize = 3; // Aumenta o tamanho dos pontos
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = Number(document.getElementById("edlStrength").value);
        tileset.pointCloudShading.eyeDomeLightingRadius = Number(document.getElementById("edlRadius").value);
        tileset.pointCloudShading.attenuation = true;
        tileset.pointCloudShading.maximumAttenuation = Number(document.getElementById("maxAttenuation").value);

        document.getElementById("lodValue").textContent = tileset.maximumScreenSpaceError;
        document.getElementById("pointSizeValue").textContent = tileset.pointCloudShading.pointSize;
        document.getElementById("edlStrengthValue").textContent = tileset.pointCloudShading.eyeDomeLightingStrength;
        document.getElementById("edlRadiusValue").textContent = tileset.pointCloudShading.eyeDomeLightingRadius;
        document.getElementById("maxAttenuationValue").textContent = tileset.pointCloudShading.maximumAttenuation;

        viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-35), 500));

        viewer.scene.postProcessStages.fxaa.enabled = true;

        // Controles de visualização
        const lodInput = document.getElementById("lod");
        const lodValue = document.getElementById("lodValue");
        lodInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.maximumScreenSpaceError = value;
            lodValue.textContent = value;
        });

        const pointSizeInput = document.getElementById("pointSize");
        const pointSizeValue = document.getElementById("pointSizeValue");
        pointSizeInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.pointSize = value;
            pointSizeValue.textContent = value;
        });

        const edlStrengthInput = document.getElementById("edlStrength");
        const edlStrengthValue = document.getElementById("edlStrengthValue");
        edlStrengthInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.eyeDomeLightingStrength = value;
            edlStrengthValue.textContent = value;
        });

        const edlRadiusInput = document.getElementById("edlRadius");
        const edlRadiusValue = document.getElementById("edlRadiusValue");
        edlRadiusInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.eyeDomeLightingRadius = value;
            edlRadiusValue.textContent = value;
        });

        const maxAttenuationInput = document.getElementById("maxAttenuation");
        const maxAttenuationValue = document.getElementById("maxAttenuationValue");
        maxAttenuationInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.maximumAttenuation = value;
            maxAttenuationValue.textContent = value;
        });

        const toggleEDLButton = document.getElementById("toggleEDL");
        toggleEDLButton.addEventListener("click", () => {
            tileset.pointCloudShading.eyeDomeLighting = !tileset.pointCloudShading.eyeDomeLighting;
        });
    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset();

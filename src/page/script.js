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
    maximumScreenSpaceError: 48, // Default LOD from slider
    maximumMemoryUsage: 2048,
    skipLevelOfDetail: false,
    preferLeaves: false, 
}

async function carregarTileset() {
    try {
        const tileset = await Cesium.Cesium3DTileset.fromUrl("http://localhost:8000/3dTilesPointCloud/tileset.json", options);

        viewer.scene.primitives.add(tileset);

        // --- Configurações Iniciais e Sincronização dos Sliders ---
        tileset.maximumScreenSpaceError = Number(document.getElementById("lod").value);
        tileset.pointCloudShading.pointSize = Number(document.getElementById("pointSize").value);
        tileset.pointCloudShading.eyeDomeLighting = true;
        tileset.pointCloudShading.eyeDomeLightingStrength = Number(document.getElementById("edlStrength").value);
        tileset.pointCloudShading.eyeDomeLightingRadius = Number(document.getElementById("edlRadius").value);
        tileset.pointCloudShading.attenuation = true;
        tileset.pointCloudShading.maximumAttenuation = Number(document.getElementById("maxAttenuation").value);

        // Sincroniza os valores dos spans
        document.getElementById("lodValue").textContent = tileset.maximumScreenSpaceError;
        document.getElementById("pointSizeValue").textContent = tileset.pointCloudShading.pointSize;
        document.getElementById("edlStrengthValue").textContent = tileset.pointCloudShading.eyeDomeLightingStrength;
        document.getElementById("edlRadiusValue").textContent = tileset.pointCloudShading.eyeDomeLightingRadius;
        document.getElementById("maxAttenuationValue").textContent = tileset.pointCloudShading.maximumAttenuation;


        viewer.zoomTo(tileset);
        viewer.scene.postProcessStages.fxaa.enabled = true;

        tileset.tileFailed.addEventListener(function (error) {
            console.error("Falha ao carregar tile:", error);
        });

        // --- Controles de visualização ---
        const lodInput = document.getElementById("lod");
        const lodValue = document.getElementById("lodValue");
        lodInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.maximumScreenSpaceError = value;
            lodValue.textContent = value;
            viewer.scene.requestRender();
        });

        const pointSizeInput = document.getElementById("pointSize");
        const pointSizeValue = document.getElementById("pointSizeValue");
        pointSizeInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.pointSize = value;
            pointSizeValue.textContent = value;
            viewer.scene.requestRender();
        });

        const edlStrengthInput = document.getElementById("edlStrength");
        const edlStrengthValue = document.getElementById("edlStrengthValue");
        edlStrengthInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.eyeDomeLightingStrength = value;
            edlStrengthValue.textContent = value;
            viewer.scene.requestRender();
        });

        const edlRadiusInput = document.getElementById("edlRadius");
        const edlRadiusValue = document.getElementById("edlRadiusValue");
        edlRadiusInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.eyeDomeLightingRadius = value;
            edlRadiusValue.textContent = value;
            viewer.scene.requestRender();
        });

        const maxAttenuationInput = document.getElementById("maxAttenuation");
        const maxAttenuationValue = document.getElementById("maxAttenuationValue");
        maxAttenuationInput.addEventListener("input", (e) => {
            const value = Number(e.target.value);
            tileset.pointCloudShading.maximumAttenuation = value;
            maxAttenuationValue.textContent = value;
            viewer.scene.requestRender();
        });

        const toggleEDLButton = document.getElementById("toggleEDL");
        toggleEDLButton.addEventListener("click", () => {
            tileset.pointCloudShading.eyeDomeLighting = !tileset.pointCloudShading.eyeDomeLighting;
            viewer.scene.requestRender();
        });

    } catch (error) {
        console.error("Erro ao carregar o tileset:", error);
    }
}

carregarTileset()
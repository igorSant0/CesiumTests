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


async function carregarGeoJSON() {
    try {
        const response = await fetch("http://localhost:8000/segmentation/mask.geojson");
        const geojson = await response.json();

        for (const feature of geojson.features) {
            if (!feature.geometry || !feature.geometry.coordinates) {
                continue;
            }

            // Handle MultiPolygon and Polygon
            const polygons = feature.geometry.type === 'MultiPolygon'
                ? feature.geometry.coordinates
                : [feature.geometry.coordinates];

            for (const polygon of polygons) {
                const coordinates = polygon[0]; // Get the exterior ring

                if (!coordinates || coordinates.length < 3) {
                    console.warn("GeoJSON feature has a polygon with less than 3 coordinates.");
                    continue;
                }

                // --- The rest of the logic is the same, but inside the loop ---

                // Calculate center
                let lon = 0;
                let lat = 0;
                coordinates.forEach(coord => {
                    lon += coord[0];
                    lat += coord[1];
                });
                const centerLon = lon / coordinates.length;
                const centerLat = lat / coordinates.length;

                const centerCartesian = Cesium.Cartesian3.fromDegrees(centerLon, centerLat);
                const clampedCartesian = await viewer.scene.clampToHeight(centerCartesian);

                let height;
                if (clampedCartesian) {
                    const clampedCartographic = Cesium.Cartographic.fromCartesian(clampedCartesian);
                    height = clampedCartographic.height;
                    console.log("Determined polygon height:", height);
                }

                if (clampedCartesian && height !== undefined && height !== null && !isNaN(height)) {
                    const positionsWithHeight = coordinates.map(coord => 
                        Cesium.Cartesian3.fromDegrees(coord[0], coord[1], height)
                    );
                    const polygonHierarchy = new Cesium.PolygonHierarchy(positionsWithHeight);
                    
                    viewer.entities.add({
                        polygon: {
                            hierarchy: polygonHierarchy,
                            material: Cesium.Color.PINK.withAlpha(0.5),
                            outline: true,
                            outlineColor: Cesium.Color.HOTPINK,
                            outlineWidth: 3
                        }
                    });
                } else {
                    console.warn("Could not determine a valid height for a polygon. Clamping to ground.");
                    const positions = Cesium.Cartesian3.fromDegreesArray(coordinates.flat());
                    const polygonHierarchy = new Cesium.PolygonHierarchy(positions);
                    
                    viewer.entities.add({
                        polygon: {
                            hierarchy: polygonHierarchy,
                            material: Cesium.Color.PINK.withAlpha(0.5),
                            outline: true,
                            outlineColor: Cesium.Color.HOTPINK,
                            outlineWidth: 3,
                            clampToGround: true
                        }
                    });
                }
            }
        }
    } catch (error) {
        console.error("Erro ao carregar o GeoJSON:", error);
    }
}

async function load() {
    await carregarTileset();
    await carregarGeoJSON();
}

load();
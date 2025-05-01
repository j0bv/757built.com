// Initialize the map centered on Hampton Roads region
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    
    // Make map globally available for the dashboard toggle
    window.map = map;
});

const map = L.map('map', {
    center: [36.9095, -76.2046],
    zoom: 10,
    minZoom: 9,
    maxZoom: 18,
    maxBoundsViscosity: 1.0,
    attributionControl: false,
    zoomControl: true,
    dragging: true,
    scrollWheelZoom: true,
    bounceAtZoomLimits: false, // Prevent bouncing at zoom limits
    zoomSnap: 0.5, // Allow finer zoom levels
    zoomDelta: 0.5
});

// Marker cluster group
const clusterGroup = L.markerClusterGroup();
map.addLayer(clusterGroup);

// Helper to convert any [lon, lat] to [lat, lon]
function toLatLng(coords) {
    if (!Array.isArray(coords) || coords.length !== 2) return coords;
    const [a, b] = coords;
    // crude check: lat is between -90..90
    return (a >= -90 && a <= 90) ? [a, b] : [b, a];
}

// Add a regular OpenStreetMap tile layer
const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: ''
}).addTo(map);

// Colors for city polygons
const cityColor = '#2b3b80'; // Navy blue for regular localities
const sevenCitiesColor = '#d32f2f'; // Red for the Seven Cities
const cityOutline = '#ffffff'; // White outline
const cityOpacity = 0.05; // Very light fill for better map visibility
const sevenCitiesOpacity = 0.15; // Slightly higher opacity for Seven Cities
const cityWeight = 2; // Slightly thicker border

// Define the Hampton Roads cities/localities
const hamptonRoadsCities = [
    "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
    "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
    "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
    "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
];

// Define the Seven Cities specifically
const sevenCities = [
    "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
    "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
];

// Function to fetch GeoJSON data for Hampton Roads localities
async function fetchHamptonRoadsData() {
    const baseUrl = 'https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Admin_Boundaries/FeatureServer/1/query';
    
    // Build query parameters
    const params = new URLSearchParams({
        where: `NAME IN ('${hamptonRoadsCities.join("','")}') AND NAME <> 'FRANKLIN COUNTY'`,
        outFields: 'NAME,JURISTYPE',
        returnGeometry: true,
        f: 'geojson'
    }).toString();
    
    try {
        const response = await fetch(`${baseUrl}?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Check for Smithfield specifically
        const hasSmithfield = data.features.some(feature => 
            feature.properties && feature.properties.NAME === "SMITHFIELD"
        );
        
        if (!hasSmithfield) {
            console.warn("Smithfield not found in initial query. Attempting to fetch it separately.");
            
            // Try to fetch Smithfield separately
            const smithfieldParams = new URLSearchParams({
                where: `NAME = 'SMITHFIELD'`,
                outFields: 'NAME,JURISTYPE',
                returnGeometry: true,
                f: 'geojson'
            }).toString();
            
            const smithfieldResponse = await fetch(`${baseUrl}?${smithfieldParams}`);
            if (smithfieldResponse.ok) {
                const smithfieldData = await smithfieldResponse.json();
                if (smithfieldData.features && smithfieldData.features.length > 0) {
                    // Add Smithfield to the data
                    data.features = data.features.concat(smithfieldData.features);
                    console.log("Successfully added Smithfield to the map data.");
                }
            }
        }
        
        // Store in global variable for other components to use
        window.currentGeoJson = data;
        
        return data;
    } catch (error) {
        console.error('Error fetching GeoJSON data:', error);
        return null;
    }
}

// Function to style the GeoJSON features
function styleFeature(feature) {
    // Check if the feature is one of the Seven Cities
    const isSevenCity = feature.properties && 
                        feature.properties.NAME && 
                        sevenCities.includes(feature.properties.NAME);
    
    return {
        fillColor: isSevenCity ? sevenCitiesColor : cityColor,
        fillOpacity: isSevenCity ? sevenCitiesOpacity : cityOpacity,
        color: cityOutline,
        weight: cityWeight,
        dashArray: '5,5', // Dashed border pattern
        lineCap: 'round',
        lineJoin: 'round'
    };
}

// Function to create popups for each feature
function onEachFeature(feature, layer) {
    if (feature.properties && feature.properties.NAME) {
        const name = feature.properties.NAME;
        const type = feature.properties.JURISTYPE === 'CI' ? 'City' : 'County';
        const isSevenCity = sevenCities.includes(name);
        
        layer.bindPopup(`
            <div class="popup-content">
                <h3>${name}</h3>
                <p class="jurisdiction-type">${type}</p>
                ${isSevenCity ? '<p class="seven-cities-badge">Seven Cities</p>' : ''}
            </div>
        `);

        // Add hover effect
        layer.on({
            mouseover: function(e) {
                const layer = e.target;
                const isSevenCity = feature.properties && 
                                   feature.properties.NAME && 
                                   sevenCities.includes(feature.properties.NAME);
                
                layer.setStyle({
                    fillOpacity: isSevenCity ? 0.4 : 0.2,
                    weight: 3,
                    dashArray: ''
                });
                layer.bringToFront();
            },
            mouseout: function(e) {
                const layer = e.target;
                const isSevenCity = feature.properties && 
                                   feature.properties.NAME && 
                                   sevenCities.includes(feature.properties.NAME);
                
                layer.setStyle({
                    fillOpacity: isSevenCity ? sevenCitiesOpacity : cityOpacity,
                    weight: cityWeight,
                    dashArray: '5,5'
                });
            }
        });
    }
}

// Initialize the map and load data
async function initMap() {
    try {
    // Fetch the GeoJSON data for Hampton Roads localities
    const geoJsonData = await fetchHamptonRoadsData();
    
        if (!geoJsonData) {
            console.error('Failed to load GeoJSON data');
            return;
        }

        // Create and add the GeoJSON layer for boundaries
        const geoJsonLayer = L.geoJSON(geoJsonData, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(map);

        // Fit the map to the boundaries and set max bounds with no padding
        const bounds = geoJsonLayer.getBounds();
        map.fitBounds(bounds);
        map.setMaxBounds(bounds);
        
        // If there's a mini-map in the dashboard, initialize it with the same data
        if (window.miniMap) {
            // Add the boundaries to miniMap
            L.geoJSON(geoJsonData, {
                style: styleFeature,
                onEachFeature: onEachFeature
            }).addTo(window.miniMap);
            
            // Add tile layer to miniMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: ''
            }).addTo(window.miniMap);
            
            // Fit the miniMap to the boundaries
            window.miniMap.fitBounds(bounds);
        }
        
        // Load project data from API if available
        loadProjectsData();
    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

// Load projects from API to show on the map
function loadProjectsData() {
    fetch('/api/graph/map-data')
        .then(response => response.json())
        .then(data => {
            if (data.map_nodes) {
                // Add project markers to the map
                data.map_nodes.forEach(node => {
                    if (node.coordinates && node.coordinates.length === 2) {
                        addNodeToMap(node);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading map data:', error);
            
            // For testing: Add some sample nodes if the API fails
            addSampleNodes();
        });
}

// Add sample nodes for testing when API is not available
function addSampleNodes() {
    const sampleNodes = [
        { 
            id: 'p1', 
            type: 'project', 
            label: 'Norfolk Innovation Center', 
            coordinates: [36.8508, -76.2859], 
            locality: 'NORFOLK',
            is_seven_cities: true
        },
        { 
            id: 'p2', 
            type: 'project', 
            label: 'VA Beach Research Park', 
            coordinates: [36.8429, -76.0129], 
            locality: 'VIRGINIA BEACH',
            is_seven_cities: true
        },
        { 
            id: 'r1', 
            type: 'research_paper', 
            label: 'Maritime Tech Study', 
            coordinates: [36.9786, -76.4284], 
            locality: 'HAMPTON',
            is_seven_cities: true
        },
        { 
            id: 'pat1', 
            type: 'patent', 
            label: 'Renewable Energy System', 
            coordinates: [36.7682, -76.2875], 
            locality: 'CHESAPEAKE',
            is_seven_cities: true
        }
    ];
    
    sampleNodes.forEach(node => addNodeToMap(node));
}

// Add a node to the map
function addNodeToMap(node) {
    if (!node.coordinates || node.coordinates.length !== 2) return;
    
    const [lat, lng] = toLatLng(node.coordinates);
    
    // Create marker icon based on node type
    const icon = L.divIcon({
        className: `map-marker ${node.type}-marker`,
        html: `<div class="marker-content" style="background-color: ${getNodeColor(node)};">
                <i class="fa ${getNodeIcon(node.type)}"></i>
              </div>`,
        iconSize: [30, 30]
    });
    
    // Create marker and add to cluster group
    const marker = L.marker([lat, lng], { icon })
        .bindPopup(createNodePopup(node));
    
    clusterGroup.addLayer(marker);
    
    // Also add to mini map if available
    if (window.miniClusterGroup) {
        const miniMarker = L.marker([lat, lng], { icon })
            .bindPopup(createNodePopup(node));
        window.miniClusterGroup.addLayer(miniMarker);
    }
    
    return marker;
}

// Get color for node type
function getNodeColor(node) {
    const isSevenCity = node.is_seven_cities;
    
    switch(node.type) {
        case 'project':
            return isSevenCity ? '#d32f2f' : '#3f51b5';
        case 'research_paper':
            return '#4caf50';
        case 'patent':
            return '#ff9800';
        case 'document':
            return '#607d8b';
        case 'locality':
            return isSevenCity ? '#d32f2f' : '#2b3b80';
        default:
            return '#888888';
    }
}

// Get icon for node type
function getNodeIcon(type) {
    switch(type) {
        case 'project':
            return 'fa-building';
        case 'research_paper':
            return 'fa-file-alt';
        case 'patent':
            return 'fa-certificate';
        case 'document':
            return 'fa-file';
        case 'locality':
            return 'fa-map-marker-alt';
        default:
            return 'fa-circle';
    }
}

// Create popup content for a node
function createNodePopup(node) {
    return `
        <div class="node-popup">
            <h3>${node.label || node.id}</h3>
            <div class="node-meta">
                <p><strong>Type:</strong> ${node.type}</p>
                ${node.locality ? `<p><strong>Locality:</strong> ${node.locality}</p>` : ''}
          </div>
            <div class="node-actions">
                <button onclick="selectNode('${node.id}')" class="btn btn-primary btn-sm">
                    View Details
                </button>
          </div>
        </div>
      `;
}

// Select a node for detailed view
function selectNode(nodeId) {
    // Load project details or graph visualization
    // This will be implemented to work with the GNN and Git graph
    console.log(`Selected node: ${nodeId}`);
    
    // Get the Git history if it's a project
    if (typeof loadGitGraphForMap === 'function') {
        loadGitGraphForMap(nodeId);
    } else {
        console.log("Git graph integration not available");
    }
    
    // If in dashboard mode, show details in the appropriate widget
    if (document.body.classList.contains('dashboard-mode') && 
        document.getElementById('git-graph-widget')) {
        document.getElementById('git-graph-widget').innerHTML = 
            `<div class="p-4 border rounded bg-white">
                <h4 class="text-lg font-semibold">Node Details: ${nodeId}</h4>
                <p class="mt-2">Loading details...</p>
            </div>`;
    }
}
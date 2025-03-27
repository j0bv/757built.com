// Initialize the map centered on Hampton Roads region
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

// Add a blank background tile layer
const blankLayer = L.tileLayer('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=', {
    attribution: ''
}).addTo(map);

// Colors for city polygons
const cityColor = '#2b3b80'; // Navy blue
const cityOutline = '#ffffff'; // White outline
const cityOpacity = 0.05; // Very light fill for better map visibility
const cityWeight = 2; // Slightly thicker border

// Define the Hampton Roads cities/localities
const hamptonRoadsCities = [
    "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
    "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
    "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
    "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
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
        
        return data;
    } catch (error) {
        console.error('Error fetching GeoJSON data:', error);
        return null;
    }
}

// Function to style the GeoJSON features
function styleFeature(feature) {
    return {
        fillColor: cityColor,
        fillOpacity: cityOpacity,
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
        
        layer.bindPopup(`
            <div class="popup-content">
                <h3>${name}</h3>
                <p class="jurisdiction-type">${type}</p>
            </div>
        `);

        // Add hover effect
        layer.on({
            mouseover: function(e) {
                const layer = e.target;
                layer.setStyle({
                    fillOpacity: 0.2,
                    weight: 3,
                    dashArray: ''
                });
                layer.bringToFront();
            },
            mouseout: function(e) {
                const layer = e.target;
                layer.setStyle({
                    fillOpacity: cityOpacity,
                    weight: cityWeight,
                    dashArray: '5,5'
                });
            }
        });
    }
}

// Initialize the map and load data
async function initMap() {
    // Fetch the GeoJSON data for Hampton Roads localities
    const geoJsonData = await fetchHamptonRoadsData();
    
    if (geoJsonData) {
        // Create the mask layer for detailed map
        const maskLayer = L.mask(geoJsonData, {
            style: {
                color: '#fff',
                fillColor: '#fff',
                fillOpacity: 1,
                stroke: false
            }
        });

        // Add OpenStreetMap layer that will only show within the jurisdictions
        const detailedMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '',
            mask: maskLayer
        }).addTo(map);
        
        // Store reference to the detailed map layer
        window.detailedMap = detailedMap;

        // Create and add the GeoJSON layer for boundaries
        const geoJsonLayer = L.geoJSON(geoJsonData, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(map);

        // Fit the map to the boundaries and set max bounds with no padding
        const bounds = geoJsonLayer.getBounds();
        map.fitBounds(bounds);
        map.setMaxBounds(bounds);
        
        // No longer adding city labels since they're on the underlying map
        // addCityLabels(geoJsonData);
    } else {
        console.error('Failed to load GeoJSON data');
    }
}

// Add L.Mask extension for masking the map
L.Mask = L.Polygon.extend({
    options: {
        stroke: false,
        color: '#fff',
        fillOpacity: 1,
        clickable: true,
        outerBounds: new L.LatLngBounds([-90, -360], [90, 360])
    },

    initialize: function (geoJson, options) {
        const outerBoundsLatLngs = [
            this.options.outerBounds.getSouthWest(),
            this.options.outerBounds.getNorthWest(),
            this.options.outerBounds.getNorthEast(),
            this.options.outerBounds.getSouthEast()
        ];
        
        // Extract all polygon coordinates from the GeoJSON
        const holes = [];
        if (geoJson && geoJson.features) {
            geoJson.features.forEach(feature => {
                if (feature.geometry && feature.geometry.coordinates) {
                    // For each feature, get the first (outer) ring of coordinates
                    if (feature.geometry.type === 'Polygon') {
                        holes.push(L.GeoJSON.coordsToLatLngs(feature.geometry.coordinates[0], 0));
                    } 
                    // For MultiPolygon, get the outer ring of each polygon
                    else if (feature.geometry.type === 'MultiPolygon') {
                        feature.geometry.coordinates.forEach(polygon => {
                            holes.push(L.GeoJSON.coordsToLatLngs(polygon[0], 0));
                        });
                    }
                }
            });
        }
        
        L.Polygon.prototype.initialize.call(this, [outerBoundsLatLngs].concat(holes), options);
    }
});

// Add mask functionality to tile layers
L.TileLayer.include({
    setMask: function(mask) {
        if (!this._container) {
            this.on('load', function() {
                this.setMask(mask);
            }, this);
            return this;
        }
        
        if (mask) {
            this._mask = mask;
            this._map.on('moveend', this._clipToMask, this);
            this._clipToMask();
        } else {
            this._map.off('moveend', this._clipToMask, this);
            this._container.style.clipPath = '';
            this._container.style.webkitClipPath = '';
        }
        return this;
    },
    
    _clipToMask: function() {
        if (!this._mask) return;
        
        const mapSize = this._map.getSize();
        const clipPoints = [];
        
        this._mask.getLatLngs()[0].forEach(function(latLng) {
            const point = this._map.latLngToContainerPoint(latLng);
            clipPoints.push([point.x, point.y]);
        }, this);
        
        // Add points for the corners of the map to ensure complete coverage
        clipPoints.push([0, 0], [mapSize.x, 0], [mapSize.x, mapSize.y], [0, mapSize.y]);
        
        const clipPath = 'polygon(' + clipPoints.map(function(point) {
            return point[0] + 'px ' + point[1] + 'px';
        }).join(', ') + ')';
        
        this._container.style.clipPath = clipPath;
        this._container.style.webkitClipPath = clipPath;
    }
});

L.mask = function (geoJson, options) {
    return new L.Mask(geoJson, options);
};

// Add mask property to tile layer options
L.TileLayer.addInitHook(function() {
    const mask = this.options.mask;
    if (mask) {
        this.on('load', function() {
            this.setMask(mask);
        }, this);
    }
});

// Start loading the map data
initMap();
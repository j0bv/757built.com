// Calendar Heatmap implementation inspired by StretchCalendarHeatmap React component
document.addEventListener('DOMContentLoaded', function() {
    // Configuration elements
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Create popup element for contributions
    const popup = document.createElement('div');
    popup.className = 'contribution-popup';
    popup.style.display = 'none';
    document.body.appendChild(popup);
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Sample data - in a real app, this would come from an API
    const sampleData = {
        2023: {
            total: 12,
            contributions: [
                { date: "2023-01-05", count: 1 },
                { date: "2023-02-15", count: 2 },
                { date: "2023-04-10", count: 3 },
                { date: "2023-06-22", count: 1 },
                { date: "2023-08-30", count: 2 },
                { date: "2023-09-15", count: 1 },
                { date: "2023-10-12", count: 3 },
                { date: "2023-11-12", count: 3 },
            ],
        },
        2024: {
            total: 8,
            contributions: [
                { date: "2024-01-20", count: 2 },
                { date: "2024-03-15", count: 1 },
                { date: "2024-05-10", count: 3 },
                { date: "2024-07-05", count: 2 },
                { date: "2024-08-12", count: 1 },
                { date: "2024-10-25", count: 2 },
                { date: "2024-12-01", count: 3 },
            ],
        },
        2025: {
            total: 10,
            contributions: [
                { date: "2025-01-15", count: 1 },
                { date: "2025-03-10", count: 1 },
                { date: "2025-03-27", count: 3 },
                { date: "2025-05-05", count: 1 },
                { date: "2025-07-20", count: 2 },
                { date: "2025-08-15", count: 1 },
                { date: "2025-10-10", count: 3 },
                { date: "2025-11-25", count: 2 },
                { date: "2025-12-24", count: 1 },
            ],
        },
        2030: {
            total: 5,
            contributions: [
                { date: "2030-01-10", count: 1 },
                { date: "2030-02-20", count: 2 },
                { date: "2030-03-15", count: 1 },
                { date: "2030-04-05", count: 3 },
                { date: "2030-05-12", count: 2 },
            ],
        }
    };
    
    // Helper function to convert sampleData to Cal-Heatmap format
    function convertToCalHeatmapFormat(year) {
        if (!sampleData[year]) return [];
        
        return sampleData[year].contributions.map(item => ({
            date: item.date,
            count: item.count
        }));
    }
    
    // Get day suffix (st, nd, rd, th)
    function getDaySuffix(day) {
        if (day > 3 && day < 21) return "th";
        switch (day % 10) {
            case 1: return "st";
            case 2: return "nd";
            case 3: return "rd";
            default: return "th";
        }
    }
    
    // Initialize the calendar
    const cal = new CalHeatmap();
    
    // Function to update the calendar
    function updateCalendar() {
        // Get data for the current year
        const data = convertToCalHeatmapFormat(currentYear);
        
        // Paint the calendar with options
        cal.paint({
            itemSelector: '#cal-heatmap',
            domain: {
                type: 'month',
                gutter: 0, // Reduced gutter to make months appear continuous
                padding: [15, 0, 0, 0]
            },
            subDomain: {
                type: 'day',
                radius: 1,
                width: 10, // Smaller width for tighter layout
                height: 10, // Smaller height for tighter layout
                gutter: 2 // Small gutter between days
            },
            date: {
                start: new Date(currentYear, 0, 1),
                highlight: 'now'
            },
            range: 12,
            scale: {
                color: {
                    range: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353', 
                           '#4ade80', '#60d394', '#88d498', '#bfd96c', '#ffe26a'], // Vibrant color scheme
                    type: 'threshold',
                    domain: [1, 2, 3, 5, 7, 10, 15, 20, 25] // More gradual color distribution
                }
            },
            data: {
                source: data,
                type: 'json',
                x: 'date',
                y: 'count',
                groupY: 'sum'
            },
            // Display tooltip on hover
            tooltip: {
                text: function(date, value, dayjsDate) {
                    if (!value || value === 0) {
                        return `No contributions on ${dayjsDate.format('MMMM D, YYYY')}`;
                    }
                    return `${value} contribution${value !== 1 ? 's' : ''} on ${dayjsDate.format('MMMM D, YYYY')}`;
                }
            }
        });
    }
    
    // Initial calendar render
    updateCalendar();
    
    // Add click event to show contribution popup
    document.querySelector('#cal-heatmap').addEventListener('click', function(e) {
        // Find the clicked cell
        const cell = e.target.closest('.ch-subdomain-bg');
        if (!cell) return;
        
        // Get the date from the cell
        const date = cell.getAttribute('data-date');
        if (!date) return;
        
        // Parse the date
        const dateObj = new Date(date);
        const day = dateObj.getDate();
        const month = dateObj.toLocaleDateString('en-US', { month: 'long' });
        
        // Get the contribution count
        const dataDate = dateObj.toISOString().split('T')[0];
        let count = 0;
        
        // Find the contribution in the yearly data
        const yearData = sampleData[currentYear];
        if (yearData) {
            const contribution = yearData.contributions.find(c => c.date === dataDate);
            if (contribution) count = contribution.count;
        }
        
        // Update popup content to match React component style
        popup.innerHTML = `
            <div>${count} contribution${count !== 1 ? 's' : ''} on ${month} ${day}${getDaySuffix(day)}.</div>
        `;
        
        // Position popup near the clicked cell
        const rect = cell.getBoundingClientRect();
        popup.style.left = `${rect.left + window.scrollX}px`;
        popup.style.top = `${rect.top + window.scrollY - 40}px`;
        
        // Show popup
        popup.style.display = 'block';
        
        // Hide popup after 3 seconds
        setTimeout(() => {
            popup.style.display = 'none';
        }, 3000);
    });
    
    // Event listeners for navigation
    prevYearBtn.addEventListener('click', function() {
        currentYear--;
        currentYearEl.textContent = currentYear;
        updateCalendar();
    });
    
    nextYearBtn.addEventListener('click', function() {
        currentYear++;
        currentYearEl.textContent = currentYear;
        updateCalendar();
    });
});

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
        
        // Create spotlight gradient effect around localities
        const spotlightMask = L.TileLayer.SpotlightMask(geoJsonData).addTo(map);

        // Create and add the GeoJSON layer for boundaries
        const geoJsonLayer = L.geoJSON(geoJsonData, {
            style: styleFeature,
            onEachFeature: onEachFeature
        }).addTo(map);

        // Fit the map to the boundaries and set max bounds with no padding
        const bounds = geoJsonLayer.getBounds();
        map.fitBounds(bounds);
        map.setMaxBounds(bounds);
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

// Add spotlight mask extension to Leaflet
L.TileLayer.SpotlightMask = function(geoJson) {
    return {
        addTo: function(map) {
            // Create SVG overlay for spotlight effect
            this._map = map;
            
            // Create SVG container for the spotlight effect
            this._container = L.SVG.create('svg');
            this._container.setAttribute('pointer-events', 'none');
            this._container.setAttribute('position', 'absolute');
            this._container.setAttribute('width', '100%');
            this._container.setAttribute('height', '100%');
            this._container.classList.add('spotlight-mask');
            
            // Add SVG filter for spotlight glow
            const filterId = 'spotlight-glow';
            const svgNS = 'http://www.w3.org/2000/svg';
            
            // Create defs element
            const defs = document.createElementNS(svgNS, 'defs');
            
            // Create filter
            const filter = document.createElementNS(svgNS, 'filter');
            filter.setAttribute('id', filterId);
            filter.setAttribute('x', '-50%');
            filter.setAttribute('y', '-50%');
            filter.setAttribute('width', '200%');
            filter.setAttribute('height', '200%');
            
            // Create filter elements
            const feGaussianBlur = document.createElementNS(svgNS, 'feGaussianBlur');
            feGaussianBlur.setAttribute('in', 'SourceGraphic');
            feGaussianBlur.setAttribute('stdDeviation', '10');
            feGaussianBlur.setAttribute('result', 'blur');
            
            const feColorMatrix = document.createElementNS(svgNS, 'feColorMatrix');
            feColorMatrix.setAttribute('in', 'blur');
            feColorMatrix.setAttribute('mode', 'matrix');
            feColorMatrix.setAttribute('values', '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7');
            feColorMatrix.setAttribute('result', 'glow');
            
            const feMerge = document.createElementNS(svgNS, 'feMerge');
            
            const feMergeNode1 = document.createElementNS(svgNS, 'feMergeNode');
            feMergeNode1.setAttribute('in', 'glow');
            
            const feMergeNode2 = document.createElementNS(svgNS, 'feMergeNode');
            feMergeNode2.setAttribute('in', 'SourceGraphic');
            
            // Add elements to structure
            feMerge.appendChild(feMergeNode1);
            feMerge.appendChild(feMergeNode2);
            
            filter.appendChild(feGaussianBlur);
            filter.appendChild(feColorMatrix);
            filter.appendChild(feMerge);
            
            defs.appendChild(filter);
            this._container.appendChild(defs);
            
            // Use a mask on the SVG for the cutout effect
            const mask = document.createElementNS(svgNS, 'mask');
            mask.setAttribute('id', 'locality-mask');
            
            // Black background rectangle for the mask
            const bgRect = document.createElementNS(svgNS, 'rect');
            bgRect.setAttribute('x', '0');
            bgRect.setAttribute('y', '0');
            bgRect.setAttribute('width', '100%');
            bgRect.setAttribute('height', '100%');
            bgRect.setAttribute('fill', 'white');
            
            mask.appendChild(bgRect);
            
            // Add each locality shape to the mask in white
            if (geoJson && geoJson.features) {
                geoJson.features.forEach(feature => {
                    if (feature.geometry && feature.geometry.coordinates) {
                        if (feature.geometry.type === 'Polygon') {
                            this._addPolygonToMask(mask, feature.geometry.coordinates, svgNS);
                        } 
                        else if (feature.geometry.type === 'MultiPolygon') {
                            feature.geometry.coordinates.forEach(polygon => {
                                this._addPolygonToMask(mask, polygon, svgNS);
                            });
                        }
                    }
                });
            }
            
            defs.appendChild(mask);
            
            // Create glow effect element that uses the mask
            const glowRect = document.createElementNS(svgNS, 'rect');
            glowRect.setAttribute('x', '0');
            glowRect.setAttribute('y', '0');
            glowRect.setAttribute('width', '100%');
            glowRect.setAttribute('height', '100%');
            glowRect.setAttribute('fill', 'rgba(43, 59, 128, 0.3)');
            glowRect.setAttribute('filter', `url(#${filterId})`);
            glowRect.setAttribute('mask', 'url(#locality-mask)');
            
            this._container.appendChild(glowRect);
            
            // Add the SVG container to the map
            map._panes.overlayPane.appendChild(this._container);
            
            // Update on map movement
            map.on('moveend', this._update, this);
            this._update();
            
            return this;
        },
        
        _addPolygonToMask: function(mask, coordinates, svgNS) {
            // Convert polygon coordinates to SVG path
            const outerRing = coordinates[0];
            if (!outerRing || outerRing.length === 0) return;
            
            const path = document.createElementNS(svgNS, 'path');
            let d = '';
            
            // Convert the GeoJSON coordinates to SVG coordinates
            outerRing.forEach((coord, i) => {
                const point = this._map.latLngToLayerPoint([coord[1], coord[0]]);
                if (i === 0) {
                    d += `M${point.x},${point.y}`;
                } else {
                    d += `L${point.x},${point.y}`;
                }
            });
            
            d += 'Z'; // Close the path
            
            path.setAttribute('d', d);
            path.setAttribute('fill', 'black');
            path.setAttribute('stroke', 'none');
            
            mask.appendChild(path);
        },
        
        _update: function() {
            // Update SVG paths when map moves
            if (this._map && this._container) {
                const mask = this._container.querySelector('#locality-mask');
                if (mask) {
                    // Remove all path elements
                    const paths = mask.querySelectorAll('path');
                    paths.forEach(path => path.remove());
                    
                    // Re-add with updated coordinates
                    const svgNS = 'http://www.w3.org/2000/svg';
                    const geoJson = window.currentGeoJson; // Store the GeoJSON globally
                    
                    if (geoJson && geoJson.features) {
                        geoJson.features.forEach(feature => {
                            if (feature.geometry && feature.geometry.coordinates) {
                                if (feature.geometry.type === 'Polygon') {
                                    this._addPolygonToMask(mask, feature.geometry.coordinates, svgNS);
                                } 
                                else if (feature.geometry.type === 'MultiPolygon') {
                                    feature.geometry.coordinates.forEach(polygon => {
                                        this._addPolygonToMask(mask, polygon, svgNS);
                                    });
                                }
                            }
                        });
                    }
                }
            }
        }
    };
};

// Add global variable to store the GeoJSON data
window.currentGeoJson = null;

// Start loading the map data
initMap();

// Fetch and display technology areas on the map
function loadTechnologyAreas() {
  fetch('/api/technology-data.php')
    .then(response => response.json())
    .then(data => {
      if (data.technology_areas) {
        data.technology_areas.forEach(area => {
          // Add a tech area marker to the appropriate city
          const coordinates = getTechAreaCoordinates(area.name);
          if (coordinates) {
            const marker = L.marker(coordinates, {
              icon: L.divIcon({
                className: 'tech-area-marker',
                html: `<div class="marker-content"><i class="fa fa-microchip"></i></div>`,
                iconSize: [40, 40]
              })
            }).addTo(map);
            
            marker.on('click', () => {
              loadTechAreaDetails(area.slug);
            });
          }
        });
      }
    })
    .catch(error => console.error('Error loading technology areas:', error));
}

// Get the coordinates for where to place tech area markers
function getTechAreaCoordinates(areaName) {
  // Map of technology areas to coordinates where the markers should appear
  const coordinates = {
    'Quantum Computing in Hampton Roads': [37.0311, -76.3452], // Jefferson Lab in Newport News
    'Renewable Energy Projects in Virginia Beach': [36.8508, -75.9779],
    'Cybersecurity Initiatives in Norfolk': [36.8507, -76.2859],
    'Maritime Technology in Hampton Roads': [36.9312, -76.3295]
    // Add more technology areas as needed
  };
  
  return coordinates[areaName];
}

// Load and display detailed information for a tech area
function loadTechAreaDetails(areaSlug) {
  fetch(`/api/technology-data.php?area=${areaSlug}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error(data.error);
        return;
      }
      
      // Create and show a popup with the technology information
      const popupContent = `
        <div class="tech-info-popup">
          <h3>${data.technology_area_name}</h3>
          
          <div class="tech-section">
            <h4>Key Role Players</h4>
            <p>${data.key_players}</p>
          </div>
          
          <div class="tech-section">
            <h4>Technological Development</h4>
            <p>${data.technological_development}</p>
          </div>
          
          <div class="tech-section">
            <h4>Project Cost</h4>
            <p>${data.project_cost}</p>
          </div>
          
          <div class="tech-section">
            <h4>Latest Update</h4>
            <p>${data.information_date ? new Date(data.information_date).toLocaleDateString() : 'Not specified'}</p>
          </div>
          
          <div class="tech-section">
            <h4>Location</h4>
            <p>${data.event_location}</p>
          </div>
          
          <div class="tech-section">
            <h4>Contact Information</h4>
            <p>${data.contact_information}</p>
          </div>
          
          <div class="tech-meta">
            <p class="small">Based on ${data.number_of_sources} sources • Updated ${new Date(data.consolidation_date).toLocaleDateString()}</p>
          </div>
        </div>
      `;
      
      // Show the popup at the appropriate location on the map
      const coordinates = getTechAreaCoordinates(data.technology_area_name);
      L.popup()
        .setLatLng(coordinates)
        .setContent(popupContent)
        .openOn(map);
    })
    .catch(error => console.error('Error loading technology details:', error));
}

// Initialize technology data when map loads
document.addEventListener('DOMContentLoaded', function() {
  // After your map is initialized
  loadTechnologyAreas();
});
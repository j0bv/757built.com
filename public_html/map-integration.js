/**
 * Map Integration for Git Graph visualization
 * 
 * This file connects the Git Graph visualization with the Leaflet map
 * from script.js, allowing projects to be displayed geographically.
 */

// Cache for loaded data
let gitGraphData = null;
let mapMarkers = {};
let clusterGroup = L.markerClusterGroup();

// Constants
const HAMPTON_ROADS_LOCALITIES = [
    "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
    "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
    "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
    "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
];

const SEVEN_CITIES = [
    "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
    "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
];

// Node type to icon mapping
const nodeTypeIcons = {
    'project': 'fa-building',
    'research_paper': 'fa-file-alt',
    'patent': 'fa-certificate',
    'document': 'fa-file',
    'person': 'fa-user',
    'funding': 'fa-dollar-sign',
    'locality': 'fa-map-marker-alt'
};

// Node type to color mapping
function getColorForNodeType(type, locality = '') {
    switch(type) {
        case 'project':
            return SEVEN_CITIES.includes(locality) ? '#d32f2f' : '#3f51b5';
        case 'research_paper':
            return '#4caf50';
        case 'patent':
            return '#ff9800';
        case 'document':
            return '#607d8b';
        case 'locality':
            return SEVEN_CITIES.includes(locality) ? '#d32f2f' : '#2b3b80';
        default:
            return '#888888';
    }
}

/**
 * Load Git Graph data for a project and add it to the map
 * @param {string} projectId - The ID of the project to visualize
 */
function loadGitGraphForMap(projectId) {
    fetch(`/api/projects/${projectId}/git-history`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            gitGraphData = data;
            addGitNodesToMap(data);
        })
        .catch(error => {
            console.error('Error loading Git graph data:', error);
        });
}

/**
 * Add Git Graph nodes to the map
 * @param {Object} data - The Git Graph data
 */
function addGitNodesToMap(data) {
    // Clear existing markers
    clearMapMarkers();
    
    // Add markers for each commit with coordinates
    data.commits.forEach(commit => {
        if (commit.coordinates && commit.coordinates.length === 2) {
            addNodeMarker(commit);
        }
    });
    
    // Add connections between nodes
    data.commits.forEach(commit => {
        if (commit.coordinates && commit.parents.length > 0) {
            commit.parents.forEach(parentId => {
                const parent = data.commits.find(c => c.id === parentId);
                if (parent && parent.coordinates) {
                    addConnectionLine(commit, parent);
                }
            });
        }
    });
    
    // Focus the map on all markers
    fitMapToMarkers();
}

/**
 * Add a marker for a node to the map
 * @param {Object} node - The node to add
 */
function addNodeMarker(node) {
    const [lat, lng] = toLatLng(node.coordinates);
    
    // Create marker
    const icon = L.divIcon({
        className: `node-marker ${node.type}-marker`,
        html: `<div class="marker-content" style="background-color: ${getColorForNodeType(node.type, node.locality)}">
                <i class="fa ${nodeTypeIcons[node.type] || 'fa-circle'}"></i>
               </div>`,
        iconSize: [30, 30]
    });
    
    const marker = L.marker([lat, lng], { icon })
        .addTo(clusterGroup)
        .bindPopup(createNodePopup(node));
    
    // Store marker reference
    mapMarkers[node.id] = marker;
    
    return marker;
}

/**
 * Create popup content for a node
 * @param {Object} node - The node to create popup for
 * @returns {string} HTML content for popup
 */
function createNodePopup(node) {
    const dateStr = node.timestamp ? new Date(node.timestamp).toLocaleDateString() : 'Unknown date';
    
    let html = `
        <div class="node-popup">
            <h3>${node.message || node.id}</h3>
            <div class="node-meta">
                <p><strong>Type:</strong> ${node.type}</p>
                <p><strong>Date:</strong> ${dateStr}</p>
    `;
    
    if (node.author && node.author !== 'Unknown') {
        html += `<p><strong>Author:</strong> ${node.author}</p>`;
    }
    
    if (node.locality) {
        html += `<p><strong>Locality:</strong> ${node.locality}</p>`;
    }
    
    if (node.cid) {
        html += `
            <p><strong>IPFS CID:</strong> 
                <a href="/ipfs/${node.cid}" target="_blank" class="cid-link">${node.cid.substring(0, 12)}...</a>
            </p>
        `;
    }
    
    html += `
            </div>
            <div class="node-actions">
                <button onclick="showGitGraph('${node.id}')" class="btn btn-sm btn-primary">
                    Show in Git Graph
                </button>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Add a connection line between two nodes
 * @param {Object} source - Source node
 * @param {Object} target - Target node
 */
function addConnectionLine(source, target) {
    if (!source.coordinates || !target.coordinates) {
        return;
    }
    
    const sourceLatLng = L.latLng(...toLatLng(source.coordinates));
    const targetLatLng = L.latLng(...toLatLng(target.coordinates));
    
    const line = L.polyline([sourceLatLng, targetLatLng], {
        color: getColorForNodeType(source.type, source.locality),
        weight: 2,
        opacity: 0.7,
        dashArray: '5, 5'
    }).addTo(map);
    
    // Store line reference
    const lineId = `line-${source.id}-${target.id}`;
    mapMarkers[lineId] = line;
}

/**
 * Clear all markers from the map
 */
function clearMapMarkers() {
    clusterGroup.clearLayers();
    Object.values(mapMarkers).forEach(marker => {
        if (marker instanceof L.Polyline) {
            map.removeLayer(marker);
        }
    });
    mapMarkers = {};
}

/**
 * Fit the map view to show all markers
 */
function fitMapToMarkers() {
    const markersList = clusterGroup.getLayers();
    
    if (markersList.length > 0) {
        const bounds = L.featureGroup(markersList).getBounds();
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

/**
 * Load projects by locality and display them on the map
 * @param {string} localityName - The name of the locality
 */
function loadProjectsByLocality(localityName) {
    fetch(`/api/projects/by-locality/${localityName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(projects => {
            if (projects.length > 0) {
                // Clear existing markers
                clearMapMarkers();
                
                // Add project markers
                projects.forEach(project => {
                    // Find locality coordinates if project doesn't have them
                    if (!project.coordinates) {
                        fetch('/api/localities')
                            .then(res => res.json())
                            .then(localities => {
                                const locality = localities.find(l => l.name === localityName);
                                if (locality && locality.coordinates) {
                                    project.coordinates = locality.coordinates;
                                    project.locality = localityName;
                                    addNodeMarker(project);
                                }
                            });
                    } else {
                        project.locality = localityName;
                        addNodeMarker(project);
                    }
                });
                
                // Add focus button to selected locality
                const popupContent = `
                    <div class="locality-popup">
                        <h3>${localityName}</h3>
                        <p>${projects.length} project(s) found</p>
                        <button onclick="showProjectsGitGraph('${localityName}')" class="btn btn-sm btn-primary">
                            Show Git Graph
                        </button>
                    </div>
                `;
                
                // Find the locality polygon and add popup
                document.querySelectorAll('.leaflet-interactive').forEach(el => {
                    if (el.__data && el.__data.properties && el.__data.properties.NAME === localityName) {
                        L.popup()
                            .setLatLng(L.latLng(projects[0].coordinates[0], projects[0].coordinates[1]))
                            .setContent(popupContent)
                            .openOn(map);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading projects by locality:', error);
        });
}

/**
 * Show Git Graph visualization for a node
 * @param {string} nodeId - The ID of the node to highlight
 */
function showGitGraph(nodeId) {
    // This function would open or focus the Git Graph visualization
    // and highlight the specified node
    console.log(`Show Git Graph for node: ${nodeId}`);
    window.open(`/git-graph.html?node=${nodeId}`, '_blank');
}

/**
 * Show Git Graph visualization for projects in a locality
 * @param {string} localityName - The name of the locality
 */
function showProjectsGitGraph(localityName) {
    console.log(`Show Git Graph for locality: ${localityName}`);
    window.open(`/git-graph.html?locality=${localityName}`, '_blank');
}

// Helper function to convert coordinate order
function toLatLng(coordinates) {
    return [coordinates[1], coordinates[0]];
}

// Initialize the integration when the map is ready
document.addEventListener('DOMContentLoaded', function() {
    // The map is initialized in script.js
    // We'll add an event handler for locality selection
    map.on('click', function(e) {
        // Check if a locality was clicked
        const layers = [];
        map.eachLayer(layer => {
            if (layer.feature && layer.feature.properties && layer.feature.properties.NAME) {
                layers.push(layer);
            }
        });
        
        // Find the closest layer to the click
        let closestLayer = null;
        let closestDistance = Infinity;
        
        layers.forEach(layer => {
            const center = layer.getBounds().getCenter();
            const distance = e.latlng.distanceTo(center);
            if (distance < closestDistance) {
                closestDistance = distance;
                closestLayer = layer;
            }
        });
        
        // If a locality was clicked and it's close enough
        if (closestLayer && closestDistance < 50000) { // 50km threshold
            const localityName = closestLayer.feature.properties.NAME;
            loadProjectsByLocality(localityName);
        }
    });
    
    // Load all map data
    fetch('/api/graph/map-data')
        .then(response => response.json())
        .then(data => {
            // We could initialize map features here
            console.log('Map data loaded:', data);
        })
        .catch(error => {
            console.error('Error loading map data:', error);
        });
}); 
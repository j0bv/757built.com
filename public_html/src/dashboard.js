// Main dashboard entry point
import Globe from 'https://unpkg.com/globe.gl@2.34.11/dist/globe.gl.js';
import { attachVirtualKeyboard } from './virtualKeyboard.js';

// Initialize components when document is loaded
document.addEventListener('DOMContentLoaded', function() {
  initDashboard();
  
  // Touch device keyboard
  if ('ontouchstart' in window) {
    attachVirtualKeyboard();
  }
});

// Initialize the dashboard's key components
function initDashboard() {
  initMiniMap();
  initGlobe();
  initKeyPlayersWidget();
  initFinanceWidget();
  initCalendarHeatmap();
  initEventHandlers();
}

// Initialize the mini-map in the dashboard widget
function initMiniMap() {
  // Create map inside dashboard map widget
  const miniMap = L.map('dashboard-map', {
    center: [36.9095, -76.2046],
    zoom: 9,
    minZoom: 8,
    maxZoom: 16,
    zoomControl: false,
    attributionControl: false,
    dragging: true,
    scrollWheelZoom: false
  });

  // Add OpenStreetMap tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: ''
  }).addTo(miniMap);

  // Store map reference for other functions
  window.dashboardMap = miniMap;
  
  // Reference VGIN ArcGIS data fetch code from original script.js
  fetchHamptonRoadsData().then(geoJsonData => {
    if (geoJsonData) {
      // Create GeoJSON layer with styling from script.js
      const geoJsonLayer = L.geoJSON(geoJsonData, {
        style: function(feature) {
          const isSevenCity = feature.properties && 
                              feature.properties.NAME && 
                              sevenCities.includes(feature.properties.NAME);
          
          return {
            fillColor: isSevenCity ? '#d32f2f' : '#2b3b80',
            fillOpacity: isSevenCity ? 0.15 : 0.05,
            color: '#ffffff',
            weight: 2,
            dashArray: '5,5'
          };
        },
        onEachFeature: function(feature, layer) {
          if (feature.properties && feature.properties.NAME) {
            const name = feature.properties.NAME;
            const type = feature.properties.JURISTYPE === 'CI' ? 'City' : 'County';
            
            layer.bindPopup(`
              <div class="popup-content">
                <h3>${name}</h3>
                <p>${type}</p>
              </div>
            `);
          }
        }
      }).addTo(miniMap);
      
      // Fit map to boundaries
      miniMap.fitBounds(geoJsonLayer.getBounds());
    }
  });
  
  // Add marker cluster for project points
  const clusterGroup = L.markerClusterGroup();
  miniMap.addLayer(clusterGroup);
  
  // Fetch project data from API and add to map
  fetch('/api/graph.json')
    .then(res => res.json())
    .then(data => {
      if (data.nodes && Array.isArray(data.nodes)) {
        data.nodes.forEach(node => {
          if (node.lat && node.lng) {
            const marker = L.marker([node.lat, node.lng], {
              icon: L.divIcon({
                className: `node-marker ${node.document_type || 'project'}-marker`,
                html: `<i class="fas ${getNodeIcon(node.document_type || 'project')}"></i>`,
                iconSize: [24, 24]
              })
            });
            
            marker.bindPopup(createNodePopup(node));
            clusterGroup.addLayer(marker);
          }
        });
      }
    })
    .catch(err => console.error('Error fetching graph data:', err));
}

// Initialize the globe in the dashboard widget
function initGlobe() {
  const globeEl = Globe()(document.getElementById('dashboard-globe'))
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
    .backgroundColor('rgba(0,0,0,0)') // Transparent background
    .showAtmosphere(true)
    .atmosphereColor('rgba(120, 120, 255, 0.3)')
    .showGraticules(false);
    
  // Position globe to show Hampton Roads
  globeEl.pointOfView({
    lat: 36.9095, 
    lng: -76.2046, 
    altitude: 2.5
  });
  
  // Fetch data and render arcs
  fetch('/api/graph.json')
    .then(res => res.json())
    .then(data => {
      const hampton = {lat: 36.9095, lng: -76.2046};
      const arcs = [];
      
      if (data.nodes && Array.isArray(data.nodes)) {
        data.nodes.forEach(n => {
          if ((n.isExternal || n.external) && n.lat && n.lng) {
            arcs.push({
              startLat: n.lat,
              startLng: n.lng,
              endLat: hampton.lat,
              endLng: hampton.lng,
              color: getArcColor(n.document_type || 'project'),
              document_type: n.document_type
            });
          }
        });
      }
      
      globeEl
        .arcsData(arcs)
        .arcColor(a => a.color)
        .arcAltitude(0.2)
        .arcStroke(0.7)
        .arcDashLength(0.9)
        .arcDashGap(4)
        .arcDashAnimateTime(4000);
    })
    .catch(err => console.error('Error loading globe data:', err));
}

// Key players widget initialization
function initKeyPlayersWidget() {
  const keyPlayersWidget = document.querySelector('#git-graph-widget');
  if (!keyPlayersWidget) return;
  
  // Placeholder for key players widget
  keyPlayersWidget.innerHTML = `
    <h3 class="text-lg font-bold mb-3 text-neon-blue">Key Project Stakeholders</h3>
    <table class="key-players-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Organization</th>
          <th>Role</th>
        </tr>
      </thead>
      <tbody id="key-players-tbody">
        <tr><td colspan="3" class="text-center">Loading stakeholders...</td></tr>
      </tbody>
    </table>
  `;
  
  // Fetch data from API
  fetch('/api/entities')
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('key-players-tbody');
      if (tbody) {
        if (data.people && data.people.length > 0) {
          tbody.innerHTML = '';
          data.people.slice(0, 8).forEach(person => {
            tbody.innerHTML += `
              <tr>
                <td>${person.name}</td>
                <td>${person.organization || '-'}</td>
                <td>${person.role || 'Contributor'}</td>
              </tr>
            `;
          });
        } else {
          tbody.innerHTML = '<tr><td colspan="3" class="text-center">No stakeholders found</td></tr>';
        }
      }
    })
    .catch(err => {
      console.error('Error fetching entities:', err);
      const tbody = document.getElementById('key-players-tbody');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">Error loading data</td></tr>';
      }
    });
}

// Finance pie chart widget
function initFinanceWidget() {
  const gnnWidget = document.querySelector('#gnn-widget');
  if (!gnnWidget) return;
  
  // Replace GNN search with funding visualization
  gnnWidget.innerHTML = `
    <h3 class="text-lg font-bold mb-3 text-neon-blue">Project Funding</h3>
    <div class="funding-stats flex justify-around items-center mb-4">
      <div class="stat-circle">
        <span class="text-2xl font-bold">$38.2M</span>
        <span class="text-xs">Total Funding</span>
      </div>
      <div class="stat-circle">
        <span class="text-2xl font-bold">24</span>
        <span class="text-xs">Funded Projects</span>
      </div>
    </div>
    <div id="funding-chart" class="h-40"></div>
  `;
  
  // We'll use Chart.js in a production app, but for now just a placeholder
  const chartDiv = document.getElementById('funding-chart');
  if (chartDiv) {
    chartDiv.innerHTML = `
      <div class="text-center text-sm">
        <div class="flex items-center justify-center gap-2 mb-2">
          <span class="inline-block w-3 h-3 bg-blue-500 rounded-full"></span>
          <span>Federal (45%)</span>
        </div>
        <div class="flex items-center justify-center gap-2 mb-2">
          <span class="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
          <span>State (28%)</span>
        </div>
        <div class="flex items-center justify-center gap-2 mb-2">
          <span class="inline-block w-3 h-3 bg-yellow-500 rounded-full"></span>
          <span>Private (27%)</span>
        </div>
      </div>
    `;
  }
}

// Calendar heatmap initialization
function initCalendarHeatmap() {
  // Use the existing cal-heatmap code, just ensure the container exists
  const calHeatmap = document.getElementById('cal-heatmap');
  if (!calHeatmap) return;
  
  // Set up calendar heatmap using the Cal-Heatmap library
  const cal = new CalHeatmap();
  cal.init({
    itemSelector: '#cal-heatmap',
    domain: 'month',
    subDomain: 'day',
    domainGutter: 5,
    range: 6,
    cellSize: 15,
    cellRadius: 2,
    tooltip: true,
    legend: [1, 3, 5, 7],
    legendColors: {
      min: '#ebedf0',
      max: var(--neon-green, '#00FF00')
    },
    data: '/api/activity?year=2025' // API endpoint for activity data
  });
  
  // Set current year in the header
  const currentYear = document.getElementById('currentYear');
  if (currentYear) {
    currentYear.textContent = '2025';
  }
  
  // Previous/Next year buttons
  const prevYear = document.getElementById('prevYear');
  const nextYear = document.getElementById('nextYear');
  
  if (prevYear) {
    prevYear.addEventListener('click', function() {
      const year = parseInt(currentYear.textContent) - 1;
      currentYear.textContent = year;
      cal.update('/api/activity?year=' + year);
    });
  }
  
  if (nextYear) {
    nextYear.addEventListener('click', function() {
      const year = parseInt(currentYear.textContent) + 1;
      currentYear.textContent = year;
      cal.update('/api/activity?year=' + year);
    });
  }
}

// Add event handlers for UI interactions
function initEventHandlers() {
  // Mode toggle button event
  const modeToggle = document.getElementById('modeToggle');
  if (modeToggle) {
    modeToggle.addEventListener('click', function() {
      document.body.classList.toggle('map-mode');
      document.body.classList.toggle('dashboard-mode');
      
      const mapContainer = document.getElementById('map-container');
      const dashboard = document.getElementById('dashboard');
      
      if (document.body.classList.contains('map-mode')) {
        mapContainer.style.display = 'block';
        dashboard.style.display = 'none';
        modeToggle.innerHTML = '<i class="fas fa-th"></i><span>Dashboard</span>';
      } else {
        mapContainer.style.display = 'none';
        dashboard.style.display = 'flex';
        modeToggle.innerHTML = '<i class="fas fa-map"></i><span>Map</span>';
      }
    });
  }
  
  // Map toggle within dashboard
  const mapToggle = document.getElementById('mapToggle');
  if (mapToggle) {
    mapToggle.addEventListener('click', function() {
      // Same as clicking the mode toggle
      if (modeToggle) modeToggle.click();
    });
  }
}

// Helper functions
function getNodeIcon(type) {
  const icons = {
    'project': 'fa-project-diagram',
    'patent': 'fa-file-certificate',
    'research': 'fa-flask',
    'person': 'fa-user',
    'organization': 'fa-building',
    'external': 'fa-external-link-alt'
  };
  return icons[type] || 'fa-file';
}

function getArcColor(type) {
  const colors = {
    'project': 'rgba(0, 200, 255, 0.7)',
    'patent': 'rgba(255, 100, 100, 0.7)',
    'research': 'rgba(100, 255, 100, 0.7)',
    'external': 'rgba(255, 255, 100, 0.7)'
  };
  return colors[type] || 'rgba(200, 200, 200, 0.7)';
}

function createNodePopup(node) {
  let title = '';
  let content = '';
  
  if (node.document_type === 'project' && node.project) {
    title = node.project.title || 'Unnamed Project';
    content = node.project.summary || '';
  } else if (node.document_type === 'patent' && node.patent) {
    title = node.patent.title || 'Unnamed Patent';
    content = `Inventors: ${node.patent.inventors || 'Unknown'}`;
  } else if (node.document_type === 'research' && node.research) {
    title = node.research.title || 'Unnamed Research';
    content = node.research.summary || '';
  } else {
    title = node.title || 'Document';
    content = node.description || '';
  }
  
  return `
    <div class="popup-content">
      <h3>${title}</h3>
      <p>${content}</p>
      <div class="node-actions">
        <button onclick="selectNode('${node.id}')" class="btn btn-sm">Details</button>
      </div>
    </div>
  `;
}

// Re-export existing variables and functions from script.js
// for mini-map function to work
const sevenCities = [
  "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
  "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
];

// Simplified helper from script.js
async function fetchHamptonRoadsData() {
  const baseUrl = 'https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Admin_Boundaries/FeatureServer/1/query';
  
  const params = new URLSearchParams({
    where: `NAME IN ('NORFOLK','VIRGINIA BEACH','CHESAPEAKE','PORTSMOUTH','SUFFOLK','HAMPTON','NEWPORT NEWS','WILLIAMSBURG','JAMES CITY','GLOUCESTER','YORK','POQUOSON','ISLE OF WIGHT','SURRY','SOUTHAMPTON','SMITHFIELD') AND NAME <> 'FRANKLIN COUNTY'`,
    outFields: 'NAME,JURISTYPE',
    returnGeometry: true,
    f: 'geojson'
  }).toString();
  
  try {
    const response = await fetch(`${baseUrl}?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching GeoJSON data:', error);
    return null;
  }
}

// Initialize the map centered on Hampton Roads region
const map = L.map('map').setView([36.9095, -76.2046], 10);

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Colors for city polygons
const cityColor = '#4CAF50';
const cityOutline = '#2b3b80';
const cityOpacity = 0.3;
const cityWeight = 2;

// Define the Hampton Roads cities/localities with their approximate coordinates
const hamptonRoadsCities = [
    { name: "NORFOLK", lat: 36.8508, lng: -76.2859 },
    { name: "VIRGINIA BEACH", lat: 36.8529, lng: -75.9780 },
    { name: "CHESAPEAKE", lat: 36.7682, lng: -76.2874 },
    { name: "PORTSMOUTH", lat: 36.8354, lng: -76.2983 },
    { name: "SUFFOLK", lat: 36.7282, lng: -76.5836 },
    { name: "HAMPTON", lat: 37.0299, lng: -76.3452 },
    { name: "NEWPORT NEWS", lat: 37.0871, lng: -76.4730 },
    { name: "WILLIAMSBURG", lat: 37.2708, lng: -76.7074 },
    { name: "JAMES CITY", lat: 37.3090, lng: -76.7698 },
    { name: "GLOUCESTER", lat: 37.4100, lng: -76.5258 },
    { name: "YORK", lat: 37.2419, lng: -76.5559 },
    { name: "POQUOSON", lat: 37.1224, lng: -76.3791 },
    { name: "SMITHFIELD", lat: 36.9824, lng: -76.6314 },
    { name: "ISLE OF WIGHT", lat: 36.9089, lng: -76.7039 },
    { name: "SURRY", lat: 37.1373, lng: -76.8752 },
    { name: "SOUTHAMPTON", lat: 36.6782, lng: -77.1024 },
    { name: "FRANKLIN", lat: 36.6776, lng: -76.9389 }
];

// Create simple circle markers for each city
hamptonRoadsCities.forEach(city => {
    // Add circle marker
    L.circle([city.lat, city.lng], {
        color: cityOutline,
        fillColor: cityColor,
        fillOpacity: cityOpacity,
        weight: cityWeight,
        radius: 5000 // 5km radius
    }).addTo(map);
    
    // Add city label
    const labelIcon = L.divIcon({
        className: 'city-label',
        html: city.name,
        iconSize: [100, 20],
        iconAnchor: [50, 10]
    });
    
    L.marker([city.lat, city.lng], {
        icon: labelIcon
    }).addTo(map);
});

// For a more accurate map, you would use GeoJSON data for the actual city boundaries
// Example of how to add GeoJSON data (if you had the actual boundary files):
/*
fetch('hampton_roads_boundaries.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            style: function(feature) {
                return {
                    color: cityOutline,
                    fillColor: cityColor,
                    fillOpacity: cityOpacity,
                    weight: cityWeight
                };
            },
            onEachFeature: function(feature, layer) {
                layer.bindPopup(feature.properties.name);
            }
        }).addTo(map);
    });
*/

// Adjust the map view to show all cities
const bounds = hamptonRoadsCities.map(city => [city.lat, city.lng]);
map.fitBounds(bounds);
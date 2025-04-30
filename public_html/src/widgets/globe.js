// globe.js - renders a mini-globe with arcs to Hampton Roads
import Globe from 'https://unpkg.com/globe.gl@2.34.11/dist/globe.gl.js';

export function initializeGlobe(apiBase = '/api/search') {
  const globeContainer = document.getElementById('dashboard-globe');
  if (!globeContainer) return;

  const globe = Globe()(globeContainer)
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
    .backgroundColor('rgba(0,0,0,0)')
    .showAtmosphere(true)
    .atmosphereColor('rgba(120, 120, 255, 0.3)')
    .showGraticules(false);

  globe.pointOfView({ lat: 36.9095, lng: -76.2046, altitude: 2.5 });

  // Fetch docs with coordinates outside HR area
  fetch(apiBase, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: '', max_results: 200 })
  })
    .then(r => r.json())
    .then(json => {
      const hampton = { lat: 36.9095, lng: -76.2046 };
      const arcs = (json.results || json.nodes || []).filter(d=>d.coordinates && d.coordinates.length===2)
        .map(n=>({
          startLat: n.coordinates[1],
          startLng: n.coordinates[0],
          endLat: hampton.lat,
          endLng: hampton.lng,
          color: 'rgba(0,200,255,0.7)'
        }));
      globe
        .arcsData(arcs)
        .arcColor(a=>a.color)
        .arcAltitude(0.2)
        .arcStroke(0.7)
        .arcDashLength(0.9)
        .arcDashGap(4)
        .arcDashAnimateTime(4000);
    })
    .catch(console.error);
}

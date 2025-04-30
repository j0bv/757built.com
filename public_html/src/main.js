import Globe from 'https://unpkg.com/globe.gl@2.34.11/dist/globe.gl.js';
import { attachVirtualKeyboard } from './virtualKeyboard.js';

const globeEl = Globe()(document.getElementById('globe'))
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
    .backgroundColor('#000');

fetch('/api/graph.json')
  .then(res => res.json())
  .then(data => {
    const hampton = {lat:36.9095,lng:-76.2046};
    const arcs = [];
    data.nodes.forEach(n=>{
      if(n.isExternal && n.lat && n.lng){
        arcs.push({
          startLat:n.lat,
          startLng:n.lng,
          endLat:hampton.lat,
          endLng:hampton.lng,
          color:'rgba(0,200,255,0.7)'
        })
      }
    });
    globeEl
      .arcsData(arcs)
      .arcColor(a=>a.color)
      .arcAltitude(0.2)
      .arcStroke(0.7)
      .arcDashLength(0.9)
      .arcDashGap(4)
      .arcDashAnimateTime(6000);
  });

// Enable virtual keyboard on touch devices
if ('ontouchstart' in window) {
  attachVirtualKeyboard();
}

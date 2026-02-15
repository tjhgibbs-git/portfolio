/**
 * Map display using Leaflet.js + OpenStreetMap tiles.
 */

var meetupMap = null;
var meetupMarkersLayer = null;

function initMap(elementId) {
    meetupMap = L.map(elementId).setView([51.505, -0.09], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
    }).addTo(meetupMap);
    meetupMarkersLayer = L.layerGroup().addTo(meetupMap);
}

function updateMapMarkers(markers) {
    if (!meetupMap || !meetupMarkersLayer) return;

    meetupMarkersLayer.clearLayers();

    if (markers.length === 0) return;

    var bounds = [];
    markers.forEach(function(m) {
        var marker = L.circleMarker([m.lat, m.lon], {
            radius: 7,
            color: '#1a5490',
            fillColor: '#4a9eff',
            fillOpacity: 0.8,
            weight: 2,
        }).bindPopup('<strong>' + m.name + '</strong>');
        meetupMarkersLayer.addLayer(marker);
        bounds.push([m.lat, m.lon]);
    });

    if (bounds.length === 1) {
        meetupMap.setView(bounds[0], 13);
    } else if (bounds.length > 1) {
        meetupMap.fitBounds(bounds, { padding: [40, 40] });
    }
}

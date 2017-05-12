var map = L.map('map', {
    crs: L.CRS.Simple,
});

var url_base = "./json/";

var tiles = L.tileLayer(
    url_base + "{z}/{x}/{y}.json",
    {
        minZoom: 0,
        maxZoom: 10,
        maxNativeZoom: 7,
        pane: "markerPane",
        detectRetina: true
    }
);
var rs = 102.5;
var rasterLayer = L.imageOverlay("raster.png", [[rs, -rs], [-rs, rs]], {
    opacity: 0.25
});

var updateZoom = function() {
    if (map.getZoom() >= 4 && map.hasLayer(rasterLayer)) {
        map.removeLayer(rasterLayer);
    }
    if (map.getZoom() <= 3 && !map.hasLayer(rasterLayer)) {
        map.addLayer(rasterLayer);
    }
    var z = map.getZoom();
    if (z >= 3) {
        rasterLayer.setOpacity(0.25);
    }
    else if (z == 2) {
        rasterLayer.setOpacity(0.33);
    }
    else {
        rasterLayer.setOpacity(0.5);
    }
};
map.on('zoomend', updateZoom);
map.on('load', updateZoom);


var svgElement = (name) => {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
};

tiles.populateTile = (tile, coords, tileSize, data) => {
    tile.setAttribute('viewBox', '0 0 512 512');
    for (const node of data) {
        var circle = svgElement('circle');
        var size = node.textSize;
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', size / 8 + 0.2);
        circle.setAttribute('class', "node lang-" + node.lang);
        tile.appendChild(circle);
    }
    for (const node of data) {
        if (node.showLabel && node.textSize >= 8) {
            var size = node.textSize;
            var label = svgElement('text');
            label.setAttribute('class', "label lang-" + node.lang);
            label.setAttribute('style', `font-size: ${node.textSize}; stroke-width: ${node.textSize / 8 + 2}`);
            label.innerHTML = node.label;
            label.setAttribute('x', node.x + node.textSize / 4 + 0.2);
            label.setAttribute('y', node.y + node.textSize * 5 / 8 + 0.2);
            tile.appendChild(label);
        }
    }
    tile.style.width = tileSize * 2;
    tile.style.height = tileSize * 2;
};

tiles.createTile = function(coords, done) {
    var tile = svgElement('svg');
    tile.setAttribute('class', 'leaflet-tile');
    var size = this.getTileSize();
    var error;

    var url = this.getTileUrl(coords);
    fetch(url).then(response => {
        if (response.ok) {
            response.json().then(data => {
                this.populateTile(tile, coords, size.x, data);
                done(error, tile);
            });
        }
    });
    return tile;
};

rasterLayer.addTo(map);
tiles.addTo(map);
map.setView(L.latLng(0, 0), 3);
var hash = new L.Hash(map);

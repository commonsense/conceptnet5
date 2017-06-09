var renderedLanguage = "mul";
if (window.location.search) {
    renderedLanguage = window.location.search.substring(1);
}
var url_base = "/vizdata/json_tiles/" + renderedLanguage + "/";

var tiles = L.tileLayer(
    url_base + "{z}/{x}/{y}.json?cache=1",
    {
        minZoom: 1,
        maxZoom: 8,
        maxNativeZoom: 7,
        pane: "overlayPane",
        detectRetina: true
    }
);
var rs = 128;
var rasterLayer = L.imageOverlay("/vizdata/raster.png", [[rs, -rs], [-rs, rs]], {
    opacity: 0.25
});

var map = L.map('map', {
    crs: L.CRS.Simple,
    renderer: L.svg()
});

var svgElement = function(name) {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
};

var popupOptions = {
    autoPan: false
};

var populateTile = function(tile, tileSize, data, zoom) {
    tile.setAttribute('viewBox', '0 0 512 512');
    for (var i=0; i < data.length; i++) {
        var node = data[i];
        if (node.s >= 4) {
            var circle = svgElement('circle');
            var size = node.s;
            var nodeSize = size * (1.25 ** (zoom - 2)) / 12 + 0.1;
            circle.setAttribute('cx', node.x);
            circle.setAttribute('cy', node.y);
            circle.setAttribute('r', nodeSize);
            circle.setAttribute('class', "node lang-" + node.lang);
            tile.appendChild(circle);
        }
    }
    for (var i=0; i < Math.min(data.length, 500); i++) {
        var node = data[i];
        if (node.label) {
            var size = node.s;
            var nodeSize = size * (1.25 ** (zoom - 2)) / 12 + 0.1;
            var url = `http://conceptnet.io${node.uri}`;
            var label = svgElement('text');
            label.setAttribute('class', "label leaflet-interactive lang-" + node.lang);
            label.setAttribute('style', `font-size: ${size}px; stroke-width: ${size / 4 + 2}px`);
            label.innerHTML = node.label;
            label.setAttribute('x', node.x + size / 4 + nodeSize);
            label.setAttribute('y', node.y + size * 5 / 8 + nodeSize);
            tile.appendChild(label);
        }
    }
    tile.style.width = tileSize * 2 + "px";
    tile.style.height = tileSize * 2 + "px";
};

tiles.createTile = function(coords, done) {
    var tile = svgElement('svg');
    tile.setAttribute('class', 'leaflet-tile');
    tile.style["z-index"] = 10000 - coords.x;
    var size = this.getTileSize();
    tile.setAttribute('data-lat', -coords.y * size.y);
    tile.setAttribute('data-lon', coords.x * size.x);

    var error;

    var url = this.getTileUrl(coords);
    if (Math.max(coords.x, coords.y, ~coords.x, ~coords.y) >= Math.pow(2, coords.z)) {
        done(error, tile);
        return tile;
    }
    fetch(url).then(function(response) {
        if (response.ok) {
            response.json().then(function(data) {
                populateTile(tile, size.x, data, coords.z);
                done(error, tile);
            });
        }
    });
    return tile;
};


var showMap = function() {
    var updateZoom = function() {
        var z = map.getZoom();
        if (z >= 4) {
            rasterLayer.setOpacity(0.15);
        }
        else if (z == 3) {
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

    if (!window.location.hash) {
        map.setView(L.latLng(0, 0), 3, {animation: false});
    }
    var hash = new L.Hash(map);

    rasterLayer.addTo(map);
    tiles.addTo(map);
};

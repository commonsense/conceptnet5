var url_base = "./json/";

var tiles = L.tileLayer(
    url_base + "{z}/{x}/{y}.json",
    {
        minZoom: 0,
        maxZoom: 10,
        maxNativeZoom: 9,
        pane: "overlayPane",
        detectRetina: true
    }
);
var rs = 128;
var rasterLayer = L.imageOverlay("raster.png", [[rs, -rs], [-rs, rs]], {
    opacity: 0.25
});

var svgElement = (name) => {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
};

var populateTile = (tile, coords, tileSize, data) => {
    tile.setAttribute('viewBox', '0 0 512 512');
    for (const node of data) {
        if (node.textSize >= 4) {
            var circle = svgElement('circle');
            var size = node.textSize;
            circle.setAttribute('cx', node.x);
            circle.setAttribute('cy', node.y);
            circle.setAttribute('r', size / 8 + 0.2);
            circle.setAttribute('class', "node lang-" + node.lang);
            tile.appendChild(circle);
        }
    }
    for (const node of data) {
        if (node.showLabel && node.textSize >= 8) {
            var size = node.textSize;
            var anchor = svgElement('a');
            anchor.setAttribute('href', `http://conceptnet.io${node.uri}`);
            var label = svgElement('text');
            label.setAttribute('class', "label leaflet-interactive lang-" + node.lang);
            label.setAttribute('style', `font-size: ${node.textSize}px; stroke-width: ${node.textSize / 8 + 2}px`);
            label.innerHTML = node.label;
            label.setAttribute('x', node.x + node.textSize / 4 + 0.2);
            label.setAttribute('y', node.y + node.textSize * 5 / 8 + 0.2);
            anchor.appendChild(label);
            tile.appendChild(anchor);
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
                populateTile(tile, coords, size.x, data);
                done(error, tile);
            });
        }
    });
    return tile;
};


var standaloneView = (element, coords) => {
    tiles._tileZoom = 7;
    var deltaNW = L.point([-2, -2]);
    var deltaSW = L.point([-2, +2]);
    var deltaNE = L.point([+2, -2]);
    var deltaSE = L.point([+2, +2]);

    var tileNW = tiles.createTile(coords.add(deltaNW), noop);
    var tileSW = tiles.createTile(coords.add(deltaSW), noop);
    var tileNE = tiles.createTile(coords.add(deltaNE), noop);
    var tileSE = tiles.createTile(coords.add(deltaSE), noop);

    tileNW.style.position = 'absolute';
    tileNW.style.top = '0px';
    tileNW.style.left = '0px';

    tileSW.style.position = 'absolute';
    tileSW.style.top = '256px';
    tileSW.style.left = '0px';

    tileNE.style.position = 'absolute';
    tileNE.style.top = '0px';
    tileNE.style.left = '256px';

    tileSE.style.position = 'absolute';
    tileSE.style.top = '256px';
    tileSE.style.left = '256px';

    element.appendChild(tileNW);
    element.appendChild(tileNE);
    element.appendChild(tileSW);
    element.appendChild(tileSE);
    return element;
};

var showMap = () => {
    var map = L.map('map', {
        crs: L.CRS.Simple,
        renderer: L.svg()
    });

    var updateZoom = function() {
        if (map.getZoom() >= 5 && map.hasLayer(rasterLayer)) {
            map.removeLayer(rasterLayer);
        }
        if (map.getZoom() <= 4 && !map.hasLayer(rasterLayer)) {
            map.addLayer(rasterLayer);
        }
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

    rasterLayer.addTo(map);
    tiles.addTo(map);
    map.setView(L.latLng(0, 0), 3);
    var hash = new L.Hash(map);
};

window.showMap = showMap;

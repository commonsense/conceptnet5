var url_base = "./json/";
var tileSize = 256;

var svgElement = function(name) {
    return document.createElementNS("http://www.w3.org/2000/svg", name);
};

var populateTile = function(tile, data) {
    for (var i=0; i < data.length; i++) {
        var node = data[i];
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
    for (var i=0; i < data.length; i++) {
        var node = data[i];
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
};

createSimpleTile = function(z, x, y) {
    var tile = svgElement('svg');
    tile.setAttribute('class', 'leaflet-tile leaflet-tile-loaded');
    var error;

    var url = "json/" + z + "/" + x + "/" + y + ".json";
    fetch(url).then(function(response) {
        if (response.ok) {
            response.json().then(function(data) {
                populateTile(tile, data);
            });
        }
    });
    reshapeTile(tile, tileSize, tileSize);
    return tile;
};


var reshapeTile = function(tile, width, height) {
    tile.style.width = width;
    tile.style.height = height;
    var svgWidth = width * 256 / tileSize;
    var svgHeight = height * 256 / tileSize;
    tile.setAttribute('viewBox', '0 0 ' + svgWidth + ' ' + svgHeight);
}


var standaloneView = function(elementName, zoom, x, y) {
    var element = document.getElementById(elementName);

    var tileNW = createSimpleTile(zoom, x - 1, y - 1);
    var tileSW = createSimpleTile(zoom, x - 1, y);
    var tileNE = createSimpleTile(zoom, x, y - 1);
    var tileSE = createSimpleTile(zoom, x, y);

    // Expand tiles so labels are only cut off at the edge of the view
    reshapeTile(tileNW, tileSize * 2, tileSize * 2);
    reshapeTile(tileSW, tileSize * 2, tileSize);
    reshapeTile(tileNE, tileSize, tileSize * 2);
    reshapeTile(tileSE, tileSize, tileSize);

    var myTiles = [tileNW, tileNE, tileSW, tileSE];
    for (var i=0; i < myTiles.length; i++) {
        var tile = myTiles[i];
        tile.style.position = 'absolute';
        element.appendChild(tile);
    }

    tileNW.style.top = '0px';
    tileNW.style.left = '0px';

    tileSW.style.top = tileSize + 'px';
    tileSW.style.left = '0px';

    tileNE.style.top = '0px';
    tileNE.style.left = tileSize + 'px';

    tileSE.style.top = tileSize + 'px';
    tileSE.style.left = tileSize + 'px';

    return element;
};


var standaloneViewFromQuery = function(elementName) {
    var query = window.location.search.substring(1);
    var parts = query.split('/');
    var z = parseInt(parts[0]);
    var x = parseInt(parts[1]);
    var y = parseInt(parts[2]);
    return standaloneView(elementName, z, x, y);
}
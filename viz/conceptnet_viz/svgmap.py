import svgwrite
import pathlib
import pycairo

from conceptnet5.vectors.formats import load_hdf


LANGUAGE_COLORS = {
    'en': '#048',
    'fr': '#76e',
    'de': '#222',
    'es': '#db0',
    'it': '#8c8',
    'ru': '#840',
    'pt': '#080',
    'ja': '#f66',
    'zh': '#a10',
    'nl': '#e70'
}


def get_concept_degrees(filename):
    concept_degrees = {}
    with open(filename, encoding='utf-8') as infile:
        for line in infile:
            line = line.strip()
            if line:
                numstr, uri = line.split(' ', 1)
                count = int(numstr)
                if count == 1:
                    break
                concept_degrees[uri] = count
    return concept_degrees


def language_and_word(uri):
    _, _c, lang, word = uri.split('/', 3)
    word = word.replace('_', ' ')
    return lang, word


def delangtag(uri):
    return uri.split('/')[3].replace('_', ' ')


def map_to_svg_coordinate(coord):
    return coord * 320 + 8192


def map_to_tile_coordinates(coord, z, threshold):
    x, y = map_to_svg_coordinate(coord)
    tile_size = 16384 >> z
    tile_x = int(x // tile_size)
    tile_y = int(y // tile_size)
    offset_x = x % tile_size
    offset_y = y % tile_size
    prop_x = offset_x / tile_size
    prop_y = offset_y / tile_size
    yield (tile_x, tile_y, offset_x, offset_y)
    if prop_x > threshold:
        yield (tile_x + 1, tile_y, offset_x - tile_size, offset_y)
    if prop_y > threshold:
        yield (tile_x, tile_y + 1, offset_x, offset_y - tile_size)
    if prop_x > threshold and prop_y > threshold:
        yield (tile_x + 1, tile_y + 1, offset_x - tile_size, offset_y - tile_size)


def draw_tsne(tsne_filename, degree_filename, svg_out_path, depth=8):
    tsne_frame = load_hdf(tsne_filename)
    svg_out_path = pathlib.Path(svg_out_path)
    concept_degrees = get_concept_degrees(degree_filename)

    tiles = {}
    for tile_z in range(depth):
        for tile_x in range(1 << tile_z + 1):
            for tile_y in range(1 << tile_z + 1):
                tiles[tile_z, tile_x, tile_y] = svgwrite.Drawing(size=(16384 >> tile_z, 16384 >> tile_z))

    print('Drawing nodes')
    for i, uri in enumerate(tsne_frame.index):
        deg = concept_degrees.get(uri, 0)
        coord = tsne_frame.iloc[i, :2]
        for z in range(depth):
            if deg >= (512 >> z):
                for tile_x, tile_y, offset_x, offset_y in map_to_tile_coordinates(coord, z, .95):
                    tile = tiles[z, tile_x, tile_y]
                    pt_size = deg ** .25 * 8 / (z + 1)
                    lang, label = language_and_word(uri)
                    color = LANGUAGE_COLORS[lang]
                    circle = tile.circle(
                        center=(offset_x, offset_y), r=pt_size, opacity=0.5,
                        style="fill: %s;" % color
                    )
                    tile.add(circle)

    print('Drawing labels')
    for i, uri in enumerate(tsne_frame.index):
        deg = concept_degrees.get(uri, 0)
        coord = tsne_frame.iloc[i, :2]
        for z in range(depth):
            if deg >= (4096 >> z):
                for tile_x, tile_y, offset_x, offset_y in map_to_tile_coordinates(coord, z, .6):
                    tile = tiles[z, tile_x, tile_y]
                    text_size = deg ** .5 * 8 / (z + 1)
                    tile_size = 16384 >> z
                    text_size = min(tile_size / 16, text_size)

                    lang, label = language_and_word(uri)
                    if z == 3:
                        print(lang, label)
                    color = LANGUAGE_COLORS[lang]
                    style = "font-family: 'Noto Sans'; font-size: %4.4fpx; fill: %s;" % (text_size, color)
                    pt_size = deg ** .25 * 8 / (z + 1)
                    text = tile.text(label, (offset_x + pt_size, offset_y + pt_size + text_size / 2), style=style)
                    tile.add(text)

    for key, val in tiles.items():
        tile_z, tile_x, tile_y = key
        out_path = svg_out_path / str(tile_z) / str(tile_x) / ("%s.svg" % tile_y)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        val.saveas(str(out_path))


if __name__ == '__main__':
    draw_tsne('viz/tsne-multi.h5', 'data/stats/concept_counts.txt', 'viz/svg')

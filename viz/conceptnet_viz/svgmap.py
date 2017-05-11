import svgwrite
import pathlib
import math
import numpy as np
from operator import itemgetter
import cairocffi as cairo

from conceptnet5.vectors.formats import load_hdf


TAU = 2 * math.pi


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


def hex_to_rgb(hexcolor):
    r = int(hexcolor[1], 16) / 15
    g = int(hexcolor[2], 16) / 15
    b = int(hexcolor[3], 16) / 15
    return r, g, b


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


def map_to_tile_coordinates(coord, z, width, height):
    x, y = map_to_svg_coordinate(coord)
    tile_size = 16384 >> z
    tile_x = int((x - 16) // tile_size)
    tile_y = int((y - 16) // tile_size)
    offset_x = x - (tile_x * tile_size)
    offset_y = y - (tile_y * tile_size)
    prop_x = (offset_x + width) / tile_size
    prop_y = (offset_y + height) / tile_size
    if tile_x >= 0 and tile_y >= 0:
        yield (tile_x, tile_y, offset_x, offset_y)
    if tile_x >= -1 and tile_y >= 0 and prop_x > 1:
        yield (tile_x + 1, tile_y, offset_x - tile_size, offset_y)
    if tile_x >= 0 and tile_y >= -1 and prop_y > 1:
        yield (tile_x, tile_y + 1, offset_x, offset_y - tile_size)
    if tile_x >= -1 and tile_y >= -1 and prop_x > 1 and prop_y > 1:
        yield (tile_x + 1, tile_y + 1, offset_x - tile_size, offset_y - tile_size)


def draw_tsne(tsne_filename, degree_filename, svg_out_path, png_out_path, render_png=False, depth=8):
    tsne_frame = load_hdf(tsne_filename)
    svg_out_path = pathlib.Path(svg_out_path)
    concept_degrees = get_concept_degrees(degree_filename)

    tiles = {}
    for tile_z in range(depth):
        for tile_x in range(1 << tile_z + 1):
            for tile_y in range(1 << tile_z + 1):
                tiles[tile_z, tile_x, tile_y] = svgwrite.Drawing(size=(16384 >> tile_z, 16384 >> tile_z))

    occlusion = np.zeros((depth, 4096, 4096), np.bool)

    print('Laying out nodes')
    nodes = []
    for i, uri in enumerate(tsne_frame.index):
        deg = min(10000, concept_degrees.get(uri, 0))
        coord = tsne_frame.iloc[i, :2]
        lang, label = language_and_word(uri)
        color = LANGUAGE_COLORS[lang]
        nodes.append((deg, coord, lang, label, color))

    print('Drawing nodes')
    nodes.sort(key=itemgetter(0), reverse=True)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4096, 4096)
    ctx = cairo.Context(surface)
    ctx.scale(1/4, 1/4)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.paint()

    for deg, coord, lang, label, color in nodes:
        for z in range(depth):
            if deg >= (256 >> z):
                pt_size = deg ** .25 * 8 / (z + 1)
                for tile_x, tile_y, offset_x, offset_y in map_to_tile_coordinates(coord, z, pt_size * 2, pt_size * 2):
                    tile = tiles[z, tile_x, tile_y]
                    circle = tile.circle(
                        center=(offset_x, offset_y), r=pt_size, opacity=.5,
                        style="fill: %s;" % color
                    )
                    tile.add(circle)
        if render_png:
            ctx.new_path()
            ctx.set_source_rgba(.75, .75, .8, 1)
            cx, cy = map_to_svg_coordinate(coord)
            ctx.arc(cx, cy, min(deg, 1000) ** .25 * 4, 0, TAU)
            ctx.fill()

    if render_png:
        surface.write_to_png(png_out_path)

    print('Drawing labels')
    for deg, coord, lang, label, color in nodes:
        cx, cy = map_to_svg_coordinate(coord)

        for z in range(depth):
            tile_size = 16384 >> z
            text_size = deg ** .5 * 8 / (z + 1)
            text_size = min(tile_size / 8, text_size)
            if text_size > tile_size / 40:
                pt_size = deg ** .25 * 8 / (z + 1)

                occlude_top = int(max(0, cy // 4))
                occlude_left = int(max(0, cx // 4))
                occlude_bottom = int(occlude_top + text_size // 3)
                occlude_right = int(occlude_left + text_size * len(label) // 4)
                region = occlusion[z, occlude_top:occlude_bottom, occlude_left:occlude_right]
                if not region.any():
                    region[:, :] = True
                    if z == 3:
                        print(lang, label)
                    for tile_x, tile_y, offset_x, offset_y in map_to_tile_coordinates(coord, z, text_size * len(label), text_size):
                        tile = tiles[z, tile_x, tile_y]
                        style = "font-family: 'Noto Sans'; font-size: %4.4fpx; fill: %s; stroke-width: %4.4fpx; stroke: white; paint-order: stroke" % (
                            text_size, color, text_size / 8 + tile_size / 64
                        )
                        text = tile.text(label, (offset_x + pt_size, offset_y + pt_size + text_size / 2), style=style)
                        tile.add(text)

    for key, val in tiles.items():
        tile_z, tile_x, tile_y = key
        out_path = svg_out_path / str(tile_z) / str(tile_x) / ("%s.svg" % tile_y)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        val.saveas(str(out_path))


if __name__ == '__main__':
    draw_tsne('viz/tsne-multi.h5', 'data/stats/concept_counts.txt', 'viz/svg', 'viz/raster.png')

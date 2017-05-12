import pathlib
import math
import json
import numpy as np
from operator import itemgetter
import cairocffi as cairo

from conceptnet5.vectors.formats import load_hdf


TAU = 2 * math.pi


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


def global_coordinate(coord):
    return coord * 4


def raster_coordinate(coord):
    return (global_coordinate(coord) + 128) * 16


def map_to_tile_coordinate(coord, z):
    x, y = global_coordinate(coord)
    tile_size = 256 >> z
    tile_x = int(math.floor(x / tile_size))
    tile_y = int(math.floor(y / tile_size))
    offset_x = x - (tile_x * tile_size)
    offset_y = y - (tile_y * tile_size)
    local_x = offset_x / tile_size * 256
    local_y = offset_y / tile_size * 256
    return (tile_x, tile_y, local_x, local_y)


def draw_tsne(tsne_filename, degree_filename, json_out_path, png_out_path, render_png=False, depth=8):
    tsne_frame = load_hdf(tsne_filename)
    json_out_path = pathlib.Path(json_out_path)
    concept_degrees = get_concept_degrees(degree_filename)

    tiles = {}
    for tile_z in range(depth):
        bound = 1 << tile_z
        for tile_x in range(-bound, bound):
            for tile_y in range(-bound, bound):
                tiles[tile_z, tile_x, tile_y] = []

    occlusion = np.zeros((depth, 4096, 4096), np.bool)

    print('Laying out nodes')
    nodes = []
    for i, uri in enumerate(tsne_frame.index):
        deg = min(10000, concept_degrees.get(uri, 0))
        coord = tsne_frame.iloc[i, :2]
        lang, label = language_and_word(uri)
        nodes.append((deg, coord, lang, label))

    print('Creating nodes')
    nodes.sort(key=itemgetter(0), reverse=True)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4096, 4096)
    ctx = cairo.Context(surface)
    ctx.scale(1/4, 1/4)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.paint()

    for deg, coord, lang, label in nodes:
        for z in range(depth):
            tile_size = 256 >> z
            if deg >= tile_size:  # no reason these should be comparable, just a convenient cutoff
                tile_x, tile_y, local_x, local_y = map_to_tile_coordinate(coord, z)
                text_size = deg ** .5 * (2 ** (z / 2 - 3))
                raster_text_size = text_size * tile_size / 16

                use_label = False
                if text_size > 2:
                    cx, cy = raster_coordinate(coord)
                    occlude_top = int(max(0, cy))
                    occlude_left = int(max(0, cx))
                    occlude_bottom = int(math.ceil(occlude_top + raster_text_size * 1.25))
                    occlude_right = int(math.ceil(occlude_left + raster_text_size * len(label)))
                    region = occlusion[z, occlude_top:occlude_bottom, occlude_left:occlude_right]
                    if not region.any():
                        region[:, :] = True
                        use_label = True
                        if z == 3:
                            print(occlude_top, occlude_left, occlude_bottom, occlude_right, lang, label)

                tile = tiles[z, tile_x, tile_y]
                tile.append({
                    'x': round(local_x, 2),
                    'y': round(local_y, 2),
                    'deg': deg,
                    'lang': lang,
                    'label': label,
                    'showLabel': use_label,
                    'textSize': round(text_size, 2)
                })

        if render_png:
            ctx.new_path()
            ctx.set_source_rgba(.75, .75, .8, 1)
            cx, cy = raster_coordinate(coord)
            ctx.arc(cx, cy, min(deg, 1000) ** .25 * 4, 0, TAU)
            ctx.fill()

    if render_png:
        surface.write_to_png(png_out_path)

    print('Writing JSON')
    for key, val in tiles.items():
        tile_z, tile_x, tile_y = key
        out_path = json_out_path / str(tile_z) / str(tile_x) / ("%s.json" % tile_y)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(out_path), 'w', encoding='utf-8') as out:
            json.dump(val, out, ensure_ascii=False)


if __name__ == '__main__':
    draw_tsne('data/viz/tsne-multi.h5', 'data/stats/concept_counts.txt', 'viz/json', 'viz/raster.png')

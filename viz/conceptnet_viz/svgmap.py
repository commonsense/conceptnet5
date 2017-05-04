import svgwrite
from conceptnet5.vectors.formats import load_hdf


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


def delangtag(uri):
    return uri.split('/')[3].replace('_', ' ')


def tsne_to_svg_coordinate(coord):
    return coord * 100 + 2500


def draw_tsne(tsne_filename, degree_filename, out_filename):
    frame = load_hdf(tsne_filename)
    concept_degrees = get_concept_degrees(degree_filename)
    draw = svgwrite.Drawing(size=(5000, 5000))

    for i, uri in enumerate(frame.index):
        deg = concept_degrees.get(uri, 0)
        x = frame.ix[i, 0]
        y = frame.ix[i, 1]
        px = tsne_to_svg_coordinate(x)
        py = tsne_to_svg_coordinate(y)
        pt_size = deg ** .25
        circle = draw.circle(
            center=(px, py), r=pt_size,
            style="fill: #abe;"
        )
        draw.add(circle)

    for i, uri in enumerate(frame.index):
        deg = concept_degrees.get(uri, 0)
        x = frame.ix[i, 0]
        y = frame.ix[i, 1]
        px = tsne_to_svg_coordinate(x)
        py = tsne_to_svg_coordinate(y)
        text_size = deg ** .5 / 4
        if deg >= 100:
            label = delangtag(uri)
            print(label)
            style = "font-family: 'Noto Sans'; font-size: %4.4fpx; fill: black;" % text_size
            text = draw.text(label, (px, py), style=style)
            draw.add(text)

    draw.saveas(out_filename)


if __name__ == '__main__':
    draw_tsne('data/vectors/tsne.h5', 'data/stats/concept_counts.txt', 'conceptnet.svg')

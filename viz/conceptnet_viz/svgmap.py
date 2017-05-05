import svgwrite
from scipy.spatial import Delaunay
from scipy.spatial.distance import euclidean
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from conceptnet5.vectors.formats import load_hdf

import numpy as np


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


def spanning_tree(frame):
    coords = frame.values[:, :2]
    triangulation = Delaunay(coords)
    neighbor_indices, neighbor_indptr = triangulation.vertex_neighbor_vertices
    print(neighbor_indices[:10])
    print(neighbor_indptr[:10])
    rows = np.zeros(neighbor_indptr.shape, dtype='i')
    cols = np.zeros(neighbor_indptr.shape, dtype='i')
    distances = np.zeros(neighbor_indptr.shape, dtype='f')
    for i in range(len(coords)):
        for j in range(neighbor_indices[i], neighbor_indices[i+1]):
            neighbor = neighbor_indptr[j]
            rows[j] = i
            cols[j] = neighbor
            distances[j] = euclidean(coords[i], coords[neighbor])

    dist_matrix = csr_matrix((distances, (rows, cols)))
    print(dist_matrix.shape)
    return minimum_spanning_tree(dist_matrix)


def draw_tsne(tsne_filename, degree_filename, out_filename, xmin=0, ymin=0, xmax=5000, ymax=5000):
    tsne_frame = load_hdf(tsne_filename)
    spantree = spanning_tree(tsne_frame)

    concept_degrees = get_concept_degrees(degree_filename)
    draw = svgwrite.Drawing(size=(xmax - xmin, ymax - ymin))

    for i, uri in enumerate(tsne_frame.index):
        deg = concept_degrees.get(uri, 0)
        x = tsne_frame.iloc[i, 0]
        y = tsne_frame.iloc[i, 1]

        fill_color = "#57e"

        px = tsne_to_svg_coordinate(x)
        py = tsne_to_svg_coordinate(y)
        if xmin <= px <= xmax and ymin <= py <= ymax:
            px -= xmin
            py -= ymin
            pt_size = deg ** .25 / 4
            circle = draw.circle(
                center=(px, py), r=pt_size, opacity=0.75,
                style="fill: %s;" % fill_color
            )
            draw.add(circle)

            neighbors = spantree.indptr[spantree.indices[i]:spantree.indices[i + 1]]
            for neighbor_idx in neighbors:
                if neighbor_idx > i:
                    nx = tsne_frame.iloc[neighbor_idx, 0]
                    ny = tsne_frame.iloc[neighbor_idx, 1]
                    pnx = tsne_to_svg_coordinate(nx) - xmin
                    pny = tsne_to_svg_coordinate(ny) - ymin
                    ndeg = concept_degrees.get(tsne_frame.index[neighbor_idx], 0)
                    weight = (deg * ndeg) ** .125 / 10
                    line = draw.line(
                        (px, py),
                        (pnx, pny),
                        opacity=0.75,
                        style="stroke: #016; stroke-width: %4.4f" % weight
                    )
                    draw.add(line)

    for i, uri in enumerate(tsne_frame.index):
        deg = concept_degrees.get(uri, 0)
        x = tsne_frame.iloc[i, 0]
        y = tsne_frame.iloc[i, 1]
        px = tsne_to_svg_coordinate(x)
        py = tsne_to_svg_coordinate(y)
        if xmin <= px <= xmax and ymin <= py <= ymax:
            px -= xmin
            py -= ymin
            text_size = deg ** .5 / 4
            if deg >= 100:
                label = delangtag(uri)
                print(label)
                style = "font-family: 'Noto Sans'; font-size: %4.4fpx; fill: black;" % text_size
                text = draw.text(label, (px, py), style=style)
                draw.add(text)

    draw.saveas(out_filename)


if __name__ == '__main__':
    draw_tsne('viz/tsne-joined.h5', 'data/stats/concept_counts.txt', 'viz/svg/conceptnet-mid.svg',
              xmin=2200, xmax=2800, ymin=2200, ymax=2800)

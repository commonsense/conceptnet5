import svgwrite
import networkx as nx
import numpy as np
from networkx.exception import NetworkXError
from networkx.algorithms.mst import minimum_spanning_tree
from scipy.spatial import Delaunay
from scipy.spatial.distance import euclidean


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


def spanning_tree(frame):
    coords = frame.values[:, :2]
    triangulation = Delaunay(coords)
    neighbor_indices, neighbor_indptr = triangulation.vertex_neighbor_vertices
    print(neighbor_indices[:10])
    print(neighbor_indptr[:10])
    graph = nx.Graph()
    for i in range(len(coords)):
        for j in range(neighbor_indices[i], neighbor_indices[i+1]):
            neighbor = neighbor_indptr[j]
            distance = euclidean(coords[i], coords[neighbor])
            graph.add_edge(i, neighbor, weight=distance)

    print("Getting spanning tree")
    spantree = minimum_spanning_tree(graph)
    newgraph = nx.Graph(graph)

    for i in graph.nodes():
        neighbors = [j for j in graph.neighbors(i) if not spantree.has_edge(i, j)]
        if neighbors:
            neighbors = np.array(neighbors)
            distances = np.array(
                [euclidean(coords[i], coords[j]) for j in neighbors]
            )
            distance_sort = np.argsort(distances)
            worst_neighbors = neighbors[distance_sort[-2:]]
            for worst in worst_neighbors:
                if newgraph.has_edge(i, worst):
                    newgraph.remove_edge(i, worst)

    return newgraph


def draw_tsne(tsne_filename, degree_filename, out_filename, xmin=0, ymin=0, xmax=5000, ymax=5000):
    tsne_frame = load_hdf(tsne_filename)
    # spantree = spanning_tree(tsne_frame)
    spantree = None

    concept_degrees = get_concept_degrees(degree_filename)
    draw = svgwrite.Drawing(size=(xmax - xmin, ymax - ymin))

    print('Drawing')
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
            pt_size = deg ** .25 / 2
            circle = draw.circle(
                center=(px, py), r=pt_size, opacity=0.75,
                style="fill: %s;" % fill_color
            )
            draw.add(circle)

            if spantree is not None:
                try:
                    neighbors = spantree.neighbors(i)
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
                                style="stroke: #348; stroke-width: %4.4f" % weight
                            )
                            draw.add(line)
                except NetworkXError:
                    pass

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
              xmin=2000, xmax=3000, ymin=2000, ymax=3000)

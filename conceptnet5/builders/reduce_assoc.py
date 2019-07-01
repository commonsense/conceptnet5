"""
Implements the `reduce_assoc` builder, which filters a tab-separated list of
associations.
"""

from collections import defaultdict

import pandas as pd

from conceptnet5.relations import is_negative_relation
from conceptnet5.uri import is_concept, uri_prefix
from conceptnet5.vectors.formats import load_hdf


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return (
        ':' in uri
        or uri.count('_') >= 3
        or uri.startswith('/a/')
        or uri.count('/') <= 2
    )


class ConceptNetAssociationGraph:
    '''
    Class to hold the concept-association edge graph.
    '''

    def __init__(self):
        '''Construct a graph with no vertices or edges.'''
        self.vertex_to_neighbors = defaultdict(set)

    def add_edge(self, left, right, value, dataset, relation):
        '''Insert an edge in the graph.'''
        self.vertex_to_neighbors[left].add(right)
        self.vertex_to_neighbors[right].add(left)
        return

    def vertices(self):
        '''Returns an iterator over the vertices of the graph.'''
        return self.vertex_to_neighbors.keys()

    def find_components(self):
        '''
        Returns a dict mapping the vertices of the graph to labels,
        such that two vertices map to the same label if and only if
        they belong to the same connected component of the undirected
        graph obtained by adding the reversal of every edge to the
        graph.  (But note that this function does not modify the graph,
        i.e. it does not add any edges.)
        '''

        component_labels = {vertex: -1 for vertex in self.vertices()}
        vertices_to_examine = set(self.vertices())
        new_label = -1
        while len(vertices_to_examine) > 0:
            new_label += 1
            vertex = vertices_to_examine.pop()
            assert component_labels[vertex] == -1
            stack = [vertex]
            component_labels[vertex] = new_label
            while len(stack) > 0:
                v = stack.pop()
                for neighbor in self.vertex_to_neighbors[v]:
                    if component_labels[neighbor] != new_label:
                        assert component_labels[neighbor] == -1
                        component_labels[neighbor] = new_label
                        vertices_to_examine.discard(neighbor)
                        stack.append(neighbor)

        return component_labels

    @classmethod
    def from_csv(cls, filename, filtered_concepts=None, reject_negative_relations=True):
        """
        Reads an association file and builds an (undirected) graph from it.

        If filtered_concepts isn't None, it should be a collection of concepts,
        and only vertices from this collection and edges that link two such
        vertices will be added to the graph.  If it _is_ None (the default),
        however, please note that no such filtering will be done (i.e. the
        effective filter collection is then the universal set of concepts, not
        the empty set).

        If reject_negative_relations is True (the default), only edges not
        corresponding to negative relations will be added to the graph.
        """
        graph = cls()

        if filtered_concepts is None:
            filter_concepts = False
        else:
            filter_concepts = True

        with open(filename, encoding='utf-8') as file:
            for line in file:
                left, right, value, dataset, rel = line.rstrip().split('\t', 4)
                if concept_is_bad(left) or concept_is_bad(right):
                    continue
                if reject_negative_relations and is_negative_relation(rel):
                    continue
                fvalue = float(value)
                gleft = uri_prefix(left)
                gright = uri_prefix(right)
                if fvalue == 0:
                    continue
                if gleft == gright:
                    continue
                if filter_concepts and gleft not in filtered_concepts:
                    continue
                if filter_concepts and gright not in filtered_concepts:
                    continue
                graph.add_edge(gleft, gright, value, dataset, rel)

        return graph


class ConceptNetAssociationGraphForReduction(ConceptNetAssociationGraph):
    """
    Subclass of ConceptNetAssociationGraph specialized for use in making
    the reduced subgraph of a full set of associations.
    """

    def __init__(self):
        super().__init__()
        self.edges = []

    def add_edge(self, left, right, value, dataset, relation):
        """
        In addition to the superclass's handling of a new edge,
        saves the full edge data.
        """
        super().add_edge(left, right, value, dataset, relation)
        self.edges.append((left, right, value, dataset, relation))


def make_filtered_concepts(filename, cutoff=3, en_cutoff=3):
    """
    Takes in a file of tab-separated associations, and returns a set of
    concepts from which those which are unlikely to be useful have been
    removed.

    All concepts that occur fewer than `cutoff` times will be removed.
    All English concepts that occur fewer than `en_cutoff` times will be removed.
    """
    counts = defaultdict(int)
    with open(filename, encoding='utf-8') as file:
        for line in file:
            left, right, _value, _dataset, rel = line.rstrip().split('\t')
            if rel == '/r/SenseOf':
                pass
            else:
                gleft = uri_prefix(left)
                gright = uri_prefix(right)
                if is_concept(gright):
                    counts[gleft] += 1
                if is_concept(gleft):
                    counts[gright] += 1

    filtered_concepts = {
        concept
        for (concept, count) in counts.items()
        if (count >= en_cutoff or (not is_concept(concept) and count >= cutoff))
    }
    return filtered_concepts


def read_embedding_vocabularies(filenames):
    """
    Reads every vector embedding file in the given collection of
    filenames, and returns the union of their vocabularies.  (The
    files are assumed to be hdf5 files containing dataframes, and
    the vocabularies are their indices.
    """
    result = pd.Index([])
    for filename in filenames:
        vectors = load_hdf(filename)
        result = result.union(vectors.index)
    return result


def reduce_assoc(
    assoc_filename, embedding_filenames, output_filename, cutoff=3, en_cutoff=3
):
    """
    Takes in a file of tab-separated simple associations, and removes
    uncommon associations and associations unlikely to be useful.  Also
    requires one or more vector embedding files (from which only the
    vocabularies are used; associations involving terms that have no
    connection, no matter how distant, to the union of those vocabularies
    will be removed).

    All concepts that occur fewer than `cutoff` times will be removed.
    All English concepts that occur fewer than `en_cutoff` times will be removed.
    """

    filtered_concepts = make_filtered_concepts(
        assoc_filename, cutoff=cutoff, en_cutoff=en_cutoff
    )

    graph = ConceptNetAssociationGraphForReduction.from_csv(
        assoc_filename,
        filtered_concepts=filtered_concepts,
        reject_negative_relations=True,
    )

    component_labels = graph.find_components()

    embedding_vocab = read_embedding_vocabularies(embedding_filenames)

    # If a connected component of the conceptnet graph contains no terms
    # from any of the embedding vocabularies, there will be no way to assign
    # vectors to any of its vertices, so we remove that component from the
    # output.

    good_component_labels = set(
        label for term, label in component_labels.items() if term in embedding_vocab
    )

    with open(output_filename, 'w', encoding='utf-8') as out:
        for gleft, gright, value, dataset, rel in graph.edges:
            if component_labels[gleft] not in good_component_labels:
                continue
            if component_labels[gright] not in good_component_labels:
                continue
            line = '\t'.join([gleft, gright, value, dataset, rel])
            print(line, file=out)

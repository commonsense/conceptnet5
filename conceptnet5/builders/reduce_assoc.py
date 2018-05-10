"""
Implements the `reduce_assoc` builder, which filters a tab-separated list of
associations.
"""

from collections import defaultdict

from conceptnet5.relations import is_negative_relation
from conceptnet5.uri import is_concept, uri_prefix
from conceptnet5.vectors.formats import load_hdf
import pandas as pd


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return (':' in uri or uri.count('_') >= 3 or
            uri.startswith('/a/') or uri.count('/') <= 2)


class ConceptNetAssociationGraph:
    '''
    Class to hold the concept-association edge graph.
    '''
    def __init__(self, save_edge_list=True):
        '''Construct a graph with no vertices or edges.'''
        if save_edge_list:
            self._edge_list = list()
            self._edge_set = None
        else:
            self._edge_list = None
            self._edge_set = set()
        self.vertex_to_neighbors = defaultdict(set)
        return

    def add_edge(self, left, right, value, dataset, rel):
        '''Insert an edge in the graph.'''
        if self._edge_list is not None:
            self._edge_list.append((left, right, value, dataset, rel))
        else:
            self._edge_set.add((left, right))
        self.vertex_to_neighbors[left].add(right)
        self.vertex_to_neighbors[right].add(left)
        return

    def vertices(self):
        '''Returns an iterator over the vertices of the graph.'''
        return self.vertex_to_neighbors.keys()

    def edge_list(self):
        '''
        Returns an iterator over the edges (left, right, value, dataset, erl) 
        of the graph.  Can only be used if the graph was constructed with 
        save_edge_list=True.
        '''
        for edge in self._edge_list:
            yield edge
        return

    def edge_set(self):
        '''
        Returns an iterator over the edges (left, right) of the graph.  
        Can only be used if the graph was constructed with save_edge_list=False.
        '''
        for edge in self._edge_set:
            yield edge
        return

    def find_components(self):
        '''
        Returns a dict mapping the vertices of the graph to labels, 
        such that two vertices map to the same label if and only if 
        they belong to the same connected component of the undirected 
        graph obtained by adding the reversal of every edge to the 
        graph.  (But note that this function does not modify the graph, 
        i.e. it does not add any edges.)
        '''
        
        component_labels = {vertex : -1 for vertex in self.vertices()}
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
        concept for (concept, count) in counts.items()
        if (
            count >= en_cutoff or
            (not is_concept(concept) and count >= cutoff)
        )
    }
    return filtered_concepts


def make_conceptnet_association_graph(
        filename, save_edge_list=True,
        concept_filter=None, bad_concept=concept_is_bad,
        bad_relation=is_negative_relation):
    """
    Reads an association file and builds an (undirected) graph from it, 
    """
    graph = ConceptNetAssociationGraph(save_edge_list)
    if concept_filter is None:
        concept_filter = lambda concept: True
    if bad_concept is None:
        bad_concept = lambda concept: False
    if bad_relation is None:
        bad_relation = lambda rel: False
    
    with open(filename, encoding='utf-8') as file:
        for line in file:
            left, right, value, dataset, rel = line.rstrip().split('\t', 4)
            if bad_concept(left) or bad_concept(right) or bad_relation(rel):
                continue
            fvalue = float(value)
            gleft = uri_prefix(left)
            gright = uri_prefix(right)
            if concept_filter(gleft) and concept_filter(gright) \
               and fvalue != 0 and gleft != gright:
                graph.add_edge(gleft, gright, value, dataset, rel)
    return graph


def read_embedding_vocabularies(filenames):
    result = pd.Index([])
    for filename in filenames:
        vectors = load_hdf(filename)
        result = result.union(vectors.index)
    return result



def reduce_assoc(assoc_filename, embedding_filenames, output_filename,
                 cutoff=3, en_cutoff=3):
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

    filtered_concepts = make_filtered_concepts(assoc_filename, cutoff=cutoff,
                                               en_cutoff=en_cutoff)

    graph = make_conceptnet_association_graph(
        assoc_filename,
        concept_filter=lambda concept:
        concept in filtered_concepts,
        bad_concept=concept_is_bad,
        bad_relation=is_negative_relation)

    component_labels = graph.find_components()

    embedding_vocab = read_embedding_vocabularies(embedding_filenames)

    good_component_labels = set(label for term, label
                                in component_labels.items()
                                if term in embedding_vocab)
    
    with open(output_filename, 'w', encoding='utf-8') as out:
        for gleft, gright, value, dataset, rel in graph.edge_list():
            if component_labels[gleft] not in good_component_labels:
                continue
            if component_labels[gright] not in good_component_labels:
                continue
            line = '\t'.join([gleft, gright, value, dataset, rel])
            print(line, file=out)

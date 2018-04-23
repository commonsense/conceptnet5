"""
Implements the `reduce_assoc` builder, which filters a tab-separated list of
associations.
"""

from collections import defaultdict

from conceptnet5.relations import is_negative_relation
from conceptnet5.uri import is_concept, uri_prefix


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return (':' in uri or uri.count('_') >= 3 or
            uri.startswith('/a/') or uri.count('/') <= 2)


class Graph:
    '''
    Class to hold the concept-association edge graph.
    '''
    def __init__(self):
        '''Construct a graph with no vertices or edges.'''
        self.edge_list = list()
        self.vertex_to_neighbors = defaultdict(set)
        return

    def add_edge(self, left, right, value, dataset, rel):
        '''Insert an edge in the graph.'''
        self.edge_list.append((left, right, value, dataset, rel))
        self.vertex_to_neighbors[left].add(right)
        self.vertex_to_neighbors[right].add(left)
        return

    def vertices(self):
        '''Returns an iterator over the vertices of the graph.'''
        return self.vertex_to_neighbors.keys()

    def edges(self):
        '''Returns an iterator over the edges of the graph.'''
        for edge in self.edge_list:
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
        
        

def reduce_assoc(filename, output_filename, cutoff=3, en_cutoff=3):
    """
    Takes in a file of tab-separated simple associations, and removes
    uncommon associations and associations unlikely to be useful.

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

    graph = Graph()
    with open(filename, encoding='utf-8') as file:
        for line in file:
            left, right, value, dataset, rel = line.rstrip().split('\t', 4)
            if concept_is_bad(left) or concept_is_bad(right) or is_negative_relation(rel):
                continue
            fvalue = float(value)
            gleft = uri_prefix(left)
            gright = uri_prefix(right)
            if (
                gleft in filtered_concepts and
                gright in filtered_concepts and
                fvalue != 0
            ):
                if gleft != gright:
                    graph.add_edge(gleft, gright, value, dataset, rel)

    component_labels = graph.find_components()
    
    component_sizes = defaultdict(int)
    max_component_size = 0
    for vertex in graph.vertices():
        component_sizes[component_labels[vertex]] += 1
        if component_sizes[component_labels[vertex]] > max_component_size:
            max_component_size = component_sizes[component_labels[vertex]]

    max_size_labels = [label for label in component_sizes.keys()
                       if component_sizes[label] == max_component_size]
    assert len(max_size_labels) > 0
    if len(max_size_labels) != 1:
        print('Warning: largest component of ConceptNet graph is not unique.')
    max_size_label = min(max_size_labels)

    print('The ConceptNet graph given has {} vertices and {} components, and the largest component has size {}.'.
          format(len(graph.vertices()),
                 len(component_sizes),
                 max_component_size))

    with open(output_filename, 'w', encoding='utf-8') as out:
        for gleft, gright, value, dataset, rel in graph.edges():
            if component_labels[gleft] != max_size_label:
                continue
            if component_labels[gright] != max_size_label:
                continue
            line = '\t'.join([gleft, gright, value, dataset, rel])
            print(line, file=out)

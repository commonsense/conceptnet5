from neo4jrestclient.client import GraphDatabase, Index

def get_arguments(assertion):
    """
    Given an assertion, get its arguments as a list.
    
    Arguments are represented in the graph as edges of type 'argument', with a property
    called 'position' that will generally either be 1 or 2. (People find 1-indexing
    intuitive in this kind of situation.)
    """
    edges = assertion.relationships.outgoing(types=['argument'])[:]
    edges.sort(key = lambda edge: edge.properties['position'])
    if len(edges) > 0:
        assert edges[0].properties['position'] == 1, "Arguments of %s are not 1-indexed"
    return [edge.end for edge in edges]

def assertion_key(node):
    """
    Takes in a node representing an Assertion, and constructs a unique key by
    which it can be identified.
    """
    pass

g = GraphDatabase("http://new-caledonia.media.mit.edu:7474/db/data/")
assertion = g.nodes[383]
print get_arguments(assertion)


# Names cannot contain commas or colons.

from neo4jrestclient.client import GraphDatabase, Index

def get_args(assertion):
    """
    Given an assertion, get its arguments as a list.
    
    Arguments are represented in the graph as edges of type 'argument', with a property
    called 'position' that will generally either be 1 or 2. (People find 1-indexing
    intuitive in this kind of situation.)
    """
    edges = assertion.relationships.outgoing(types=['arg'])[:]
    edges.sort(key = lambda edge: edge.properties['position'])
    if len(edges) > 0:
        assert edges[0]['position'] == 1, "Arguments of {0} are not 1-indexed".format(assertion)
    return [edge.end for edge in edges]

def get_relation(assertion):
    edges = assertion.relationships.outgoing(types=['relation'])
    assert len(edges) == 1
    return edges[0].end

def assertion_key(node):
    """
    Takes in a node representing an Assertion, and constructs a unique key by
    which it can be identified.
    """
    rel = get_relation(node)['name']
    arg_names = [arg['name'] for arg in get_args(node)]
    arg_string = ','.join(arg_names)
    lang = node['language']
    return "/assertion/{0}/{1}:{2}".format(lang, rel, arg_string)

if __name__ == '__main__':
    g = GraphDatabase("http://new-caledonia.media.mit.edu:7474/db/data/")
    assertion = g.nodes[387]
    assertion['language'] = 'en'
    print assertion_key(assertion)     # gives /assertion/en/Has:otter,fur


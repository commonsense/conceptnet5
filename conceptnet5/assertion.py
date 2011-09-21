from neo4jrestclient.client import GraphDatabase, Index, Node
from conceptnet5.nodes import get_id, get_concept_with_id, get_relation_with_id
import json

def _list_to_id(list):
    #return json.dumps(list).replace(', ', ',')
    return ','.join(list)

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
    pieces = [get_relation(node)] + get_args(node)
    arg_ids = [get_id(piece) for piece in pieces]
    arg_string = _list_to_id(arg_ids)
    return "/assertion/"+arg_string

def _index_assertion(graph, assertion):
    if not 'assertions' in graph.nodes.indexes.keys():
        graph.nodes.indexes.create('assertions')
    index_key = assertion_key(assertion)
    graph.nodes.indexes['assertions'].add('name', index_key, assertion)

def _create_assertion(graph, language, rel, args):
    assertion = g.node(type='assertion', language=language)
    rel = _ensure_relation(graph, rel)
    args = [_ensure_concept(graph, arg) for arg in args]
    assertion.relationships.create("relation", rel)
    for i in xrange(len(args)):
        assertion.relationships.create("arg", args[i], position=i+1)
    _index_assertion(graph, assertion)
    return assertion

def _ensure_id(node):
    if isinstance(node, Node):
        return get_id(node)
    else:
        return node

def _ensure_concept(graph, node):
    if isinstance(node, basestring):
        return get_concept_with_id(graph, node)
    else:
        return node

def _ensure_relation(graph, node):
    if isinstance(node, basestring):
        return get_relation_with_id(graph, node)
    else:
        return node

def find_assertion(graph, rel, args):
    rel = _ensure_relation(graph, rel)
    args = [_ensure_concept(graph, arg) for arg in args]
    arg_ids = [get_id(arg) for arg in [rel] + args]
    arg_string = _list_to_id(arg_ids)
    index_key = "/assertion/"+arg_string

    result = graph.nodes.indexes['assertions'].query('name',index_key)[:]
    if len(result):
        return result[0]
    else:
        return None

def get_assertion(graph, language, rel, args):
    return find_assertion(graph, rel, args) or _create_assertion(graph, language, rel, args)

if __name__ == '__main__':
    g = GraphDatabase("http://new-caledonia.media.mit.edu:7474/db/data/")
    assertion = get_assertion(g, 'en', '/rel/IsA', ['/en/dog', '/en/animal'])
    print assertion_key(assertion)     



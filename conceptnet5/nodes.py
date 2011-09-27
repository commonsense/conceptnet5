"""
Julian Chaidez, ConceptNet5
_creata_concept()
_find_concept()
_get_concept()
"""

class ConceptNetGraph(object):
    def __init__(self, url)
        self.graph = GraphDatabase(url)

def create_concept(graph,language, name):
    new_concept = graph.node(type = 'concept', language = language, name = name)
    index_key = '/concept/' + language + '/' + name
    new_concept['key'] = index_key
    return new_concept

def find_concept(graph, language, name):
    index_key = '/concept/' + language + '/' + name
    return lookup_id(graph, index_key)

def get_concept_with_id(graph, id):
    _, type, lang, name = id.split('/')
    assert type == 'concept'
    return get_concept(graph, lang, name)

def get_concept(graph, language, name):
    concept = find_concept(graph, language, name)
    if not concept:
        concept = create_concept(graph, language, name)
    return concept

def create_relation(graph, name):
    new_relation = graph.node(type = 'relation', name = name)
    index_key = '/relation/' + name
    new_relation['key'] = index_key
    return new_relation

def find_relation(graph, name):
    index_key = '/relation/' + name
    return lookup_id(graph, index_key)

def get_relation_with_id(graph, id):
    _, type, name = id.split('/')
    assert type == 'relation'
    return get_relation(graph, name)

def get_relation(graph, name):
    relation = find_relation(graph, name)
    if not relation:
        relation = create_relation(graph, name)
    return relation

def lookup_id(graph, key):
    "Get the node with a particular ID, no matter what type it is."
    result = graph.nodes.indexes['node_auto_index'].query('key',key)[:]
    if len(result): return result[0]
    else: return None

def get_id(node):
    if node['type'] == 'relation': return '/relation/' + node['name']
    elif node['type'] == 'concept': return '/concept/' +  node['language'] + '/' + node['name']

# Change this URL if you're not on n-c.
g = GraphDatabase("http://localhost:7474/db/data/")

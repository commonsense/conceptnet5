"""
Julian Chaidez, ConceptNet5
_creata_concept()
_find_concept()
_get_concept()
"""

def create_concept(graph,language, name):

    new_concept = graph.node(type = 'concept', language = language, name = name)
    index_key = '/concept/' + language + '/' + name
    if not 'concepts' in graph.nodes.indexes.keys(): graph.nodes.indexes.create('concepts')
    graph.nodes.indexes['concepts']['index_key'] = new_concept
    return new_concept

def find_concept(graph, language, name):

    index_key = '/' + language + '/' + name
    index = graph.nodes.indexes['concept_index']
    result = index.query('name',index_key)[:]
    if len(result): return result[0]
    else: return None

def get_concept(graph, language, name):

    concept = find_concept(graph, language, name)
    if not concept:
        concept = create_concept(graph, language, name)
    return concept

def create_relation(graph, name):

def find_relation(graph, name):

def get_relation(graph, name):

def get_id(node):

    if node['type'] == 'relation': return '/rel/' + node['name']
    elif node['type'] == 'concept': return '/' +  node['language'] + '/' + node['name']

def 

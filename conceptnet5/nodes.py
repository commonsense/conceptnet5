"""
Julian Chaidez, ConceptNet5
_creata_concept()
_find_concept()
_get_concept()
"""

def create_concept(graph,language, name):

    new_concept = graph.node(type = 'concept', language = language, name = name)
    index_key = '/' + language + '/' + name
    if not 'concepts' in graph.nodes.indexes.keys(): graph.nodes.indexes.create('concepts')
    graph.nodes.indexes['concepts'][index_key] = new_concept
    return new_concept

def find_concept(graph, language, name):

    index_key = '/' + language + '/' + name
    result = graph.nodes.indexes['concepts'].query('name',index_key)[:]
    if len(result): return result[0]
    else: return None

def get_concept_with_id(graph, id):

    _, lang, name = id.split('/')
    return get_concept(graph, lang, name)

def get_concept(graph, language, name):

    concept = find_concept(graph, language, name)
    if not concept:
        concept = create_concept(graph, language, name)
    return concept

def create_relation(graph, name):

    new_relation = graph.node(type = 'relation', name = name)
    index_key = '/rel/' + name
    if not 'relations' in graph.nodes.indexes.keys(): graph.nodes.indexes.create('relations')
    graph.nodes.indexes['relations'][index_key] = new_relation
    return new_relation

def find_relation(graph, name):

    index_key = '/rel/' + name
    result = graph.nodes.indexes['relations'].query('tag',index_key)[:]
    if len(result): return result[0]
    else: return None

def get_relation_with_id(graph, id):

    _, rel, name = id.split('/')
    return get_relation(graph, name)

def get_relation(graph, name):

    relation = find_relation(graph, name)
    if not relation:
        relation = create_relation(graph, name)
    return relation

def get_id(node):

    if node['type'] == 'relation': return '/rel/' + node['name']
    elif node['type'] == 'concept': return '/' +  node['language'] + '/' + node['name']

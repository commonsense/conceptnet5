"""
Julian Chaidez, ConceptNet5
_creata_concept()
_find_concept()
_get_concept()
"""

def create_concept(graph,language, name):

    new_concept = graph.node(type = 'concept', language = language, name = name)
    index_key = '/' + language + '/' + name
    graph.nodes.indexes['concept_index']['index_key'] = new_concept
    return new_concept

def find_concept(graph, language, name):

    index_key = '/' + language + '/' + name
    index = graph.nodes.indexes['concept_index']
    result = index.query('name',index_key)[:])
    if len(result): return result[0]
    else: return None

def get_concept(graph, language, name):

    concept = _find_concept(graph, language, name)
    if not concept:
        concept = _create_concept(graph, language, name)
    return concept


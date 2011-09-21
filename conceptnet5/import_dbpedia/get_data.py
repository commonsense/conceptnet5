# Author: Justin Venezuela (jven@mit.edu)
"""
Get data from DBPedia.
"""

from SPARQLWrapper import SPARQLWrapper, JSON

def get_concept_from_uri(uri):
  return uri.split('/')[-1].split('#')[-1]

def get_types(concept_string):
  sparql = SPARQLWrapper('http://dbpedia.org/sparql')
  sparql.setQuery("""
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
      SELECT ?type
      WHERE {
        <http://dbpedia.org/resource/%s> rdf:type ?type .
      }
  """ % concept_string)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  type_results = results['results']['bindings']
  types = []
  for type_result in type_results:
    concept_type = get_concept_from_uri(type_result['type']['value'])
    if concept_type is not None:
      types.append(concept_type)
  return types

def main():
  concepts = ['Apple', 'Banana', 'Chess', 'Dog', 'Elevator', 'Fitzgerald',
      'Ghana']
  for concept in concepts:
    concept_types = get_types(concept)
    for concept_type in concept_types:
      print '%s is of type %s.' % (concept, concept_type)

if __name__ == '__main__':
  main()

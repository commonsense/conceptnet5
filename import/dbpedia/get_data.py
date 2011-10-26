"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu), Rob Speer (rspeer@mit.edu)'

from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize_topic, un_camel_case
import urllib
import urllib2

GRAPH = JSONWriterGraph('../json_data/dbpedia_data')

DBPEDIA_SOURCE = GRAPH.get_or_create_node('/source/web/dbpedia.org')
GRAPH.justify('/', DBPEDIA_SOURCE)

TYPE_ASSERTION_PROPERTIES = {
    'dataset':u'dbpedia',
    'license':u'CC-By-SA',
    'normalized':'False'
}
NORM_ASSERTION_PROPERTIES = {
    'dataset':u'dbpedia',
    'license':u'CC-By-SA',
    'normalized':'False'
}

VERBOSE = True
def show_message(message):
  if VERBOSE:
    print message

def normalize_topic_url(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    return normalize_topic(un_camel_case(url.strip('/').split('/')[-1].split('#')[-1]))

def map_web_relation(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    result = url.strip('/').split('/')[-1].split('#')[-1]
    if result == 'type':
        return 'InstanceOf'
    elif result == 'isPartOf':
        return 'PartOf'
    else:
        return result[0].upper() + result[1:]

def handle_file(filename):
    for line in open(filename):
        handle_triple(line.strip())

def handle_triple(line):
    items = line.split()
    for i in xrange(3):
        if not (items[i].startswith('<') and items[i].endswith('>')):
            return
        items[i] = items[i][1:-1]
    subj, pred, obj = items[:3]
    concept1, web_rel, concept2 = [GRAPH.get_or_create_web_concept(url) for url in items[:3]]
    assertion = GRAPH.get_or_create_assertion(
        web_rel, [concept1, concept2],
        properties=TYPE_ASSERTION_PROPERTIES
    )
    norm1 = GRAPH.get_or_create_concept('en', *normalize_topic_url(subj))
    norm2 = GRAPH.get_or_create_concept('en', *normalize_topic_url(obj))
    rel = GRAPH.get_or_create_relation(map_web_relation(web_rel))
    norm_assertion = GRAPH.get_or_create_assertion(
        rel, [norm1, norm2],
        properties=NORM_ASSERTION_PROPERTIES
    )
    GRAPH.justify(DBPEDIA_SOURCE, assertion)
    GRAPH.derive_normalized(assertion, norm_assertion)
    print assertion
    print norm_assertion

def main():
    handle_file('mappingbased_properties_en.nt')
    handle_file('instance_types_en.nt')

if __name__ == '__main__':
    main()

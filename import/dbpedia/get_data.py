"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu), Rob Speer (rspeer@mit.edu)'

from metanl.english import normalize_topic, un_camel_case
from conceptnet5.nodes import make_concept_uri, normalize_uri
from conceptnet5.edges import make_edge, MultiWriter, FlatEdgeWriter
import urllib
import urllib2

source = '/s/web/dbpedia.org'

writer = MultiWriter('dbpedia')
sw_map = FlatEdgeWriter('data/sw/dbpedia.map.json')
sw_map_used = set()

VERBOSE = True
def show_message(message):
  if VERBOSE:
    print message

def translate_wp_url(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    return un_camel_case(url.strip('/').split('/')[-1].split('#')[-1])

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
    if 'foaf/0.1/homepage' in pred or '_Feature' in obj or '#Thing' in obj or '__' in subj or '__' in obj: return
    subj_concept = make_concept_uri(translate_wp_url(subj), 'en')
    obj_concept = make_concept_uri(translate_wp_url(obj), 'en')
    rel = normalize_uri('/r/'+map_web_relation(pred))

    if (pred, rel) not in sw_map_used:
        sw_map_used.add((pred, rel))
        sw_map.write({'from': pred, 'to': rel})
    if (subj, subj_concept) not in sw_map_used:
        sw_map_used.add((subj, subj_concept))
        sw_map.write({'from': subj, 'to': subj_concept})
    if (obj, obj_concept) not in sw_map_used:
        sw_map_used.add((obj, obj_concept))
        sw_map.write({'from': obj, 'to': obj_concept})

    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/dbpedia/en',
                     license='/l/CC/By-SA',
                     sources=['/s/dbpedia/3.7'],
                     context='/ctx/all',
                     weight=0.5)
    writer.write(edge)

def main():
    #handle_file('mappingbased_properties_en.nt')
    handle_file('instance_types_en.nt')

if __name__ == '__main__':
    main()

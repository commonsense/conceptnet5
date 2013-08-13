"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu), Rob Speer (rspeer@mit.edu)'

from metanl.english import normalize_topic, un_camel_case
from conceptnet5.nodes import make_concept_uri, normalize_uri
from conceptnet5.edges import make_edge
import urllib
import urllib2
import json
import sys
import codecs

source = '/s/web/dbpedia.org'
sw_map_used = set()

def translate_wp_url(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    return un_camel_case(url.strip('/').split('/')[-1].split('#')[-1])

def map_web_relation(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    result = url.strip('/').split('/')[-1].split('#')[-1]
    if result == 'type':
        return 'IsA'
    elif result.startswith('isPartOf'):
        return 'PartOf'
    elif result.startswith('location'):
        return 'AtLocation'
    else:
        return None

def handle_file(filename, out_filename, map_filename):
    count = 0
    out = codecs.open(out_filename, 'w', encoding='utf-8')
    map_out = codecs.open(map_filename, 'w', encoding='utf-8')
    for line in open(filename):
        handle_triple(line.strip(), out, map_out)

def write_json(out, obj):
    print >> out, json.dumps(obj, ensure_ascii=False)

def handle_triple(line, out, map_out):
    items = line.split()
    for i in xrange(3):
        if not (items[i].startswith('<') and items[i].endswith('>')):
            return
        items[i] = items[i][1:-1]
    subj, pred, obj = items[:3]
    if 'foaf/0.1/homepage' in pred or '_Feature' in obj or '#Thing' in obj or '__' in subj or '__' in obj or 'List_of' in subj or 'List_of' in obj: return
    if 'dbpedia.org' not in obj: return
    subj_concept = make_concept_uri(translate_wp_url(subj), 'en')
    obj_concept = make_concept_uri(translate_wp_url(obj), 'en')
    if obj_concept == '/c/en/work':
        obj_concept = '/c/en/creative_work'
    webrel = map_web_relation(pred)
    if webrel is None:
        return
    rel = normalize_uri('/r/'+webrel)

    if (pred, rel) not in sw_map_used:
        sw_map_used.add((pred, rel))
        write_json(map_out, {'from': pred, 'to': rel})
    if (subj, subj_concept) not in sw_map_used:
        sw_map_used.add((subj, subj_concept))
        write_json(map_out, {'from': subj, 'to': subj_concept})
    if (obj, obj_concept) not in sw_map_used:
        sw_map_used.add((obj, obj_concept))
        write_json(map_out, {'from': obj, 'to': obj_concept})

    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/dbpedia/en',
                     license='/l/CC/By-SA',
                     sources=['/s/dbpedia/3.7'],
                     context='/ctx/all',
                     weight=0.5)
    write_json(out, edge)

if __name__ == '__main__':
    handle_file(sys.argv[1], sys.argv[2], sys.argv[3])

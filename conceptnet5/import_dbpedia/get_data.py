"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from conceptnet5.graph import get_graph
import urllib2

DBPEDIA_DATA_PREFIX = u'http://dbpedia.org/page/'
DBPEDIA_SOURCE = [u'source', u'web', u'dbpedia.org']
TYPE_RELATION = u'/relation/rdf:type'
TYPE_RELATION_PROP_KEY = u'owl:sameAs'
TYPE_RELATION_PROP_VAL = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'

VERBOSE = True

def clean_url(url):
  return url.replace('/', '_')

def show_message(message):
  if VERBOSE:
    print message

def get_url_from_obj_name(obj_name):
  show_message('NOTICE: Getting data for object \'%s\'.' % obj_name)
  obj_url = DBPEDIA_DATA_PREFIX + obj_name
  return obj_url

def get_html_from_url(url):
  show_message('NOTICE: Opening DBPedia page...')
  page = urllib2.urlopen(url)
  html = page.read()
  page.close()
  show_message('NOTICE: Done.')
  return html

def get_types_from_html(html):
  show_message('NOTICE: Parsing...')
  obj_types = []
  html = html.split('<a class="uri" href="http://www.w3.org/1999/02/'
      '22-rdf-syntax-ns#type">', 1)[1].split('<ul>', 1)[1].split('</ul>', 1)[0]
  while 'href="' in html:
    [obj_type, html] = html.split('href="', 1)[1].split('">', 1)
    obj_types.append(obj_type)
  show_message('NOTICE: Done.')
  return obj_types

def make_type_assertions_for_obj(conceptnet, obj_url, obj_types):
  concept = conceptnet.get_or_create_node(obj_url)
  print concept
  return
  relation = conceptnet.get_or_create_relation(TYPE_RELATION)
  source = conceptnet.get_or_create_source(DBPEDIA_SOURCE)
  relation[TYPE_RELATION_PROP_KEY] = TYPE_RELATION_PROP_VAL
  for obj_type in obj_types:
    obj_type_concept = conceptnet.get_or_create_node(obj_type)
    assertion = conceptnet.get_or_create_assertion(
        TYPE_RELATION, concept, obj_type_concept)
    conceptnet.justify(source, assertion)

def main():
  conceptnet = get_graph()
  obj_names = ['Tetris']
  for obj_name in obj_names:
    # get data from dbpedia
    obj_url = get_url_from_obj_name(obj_name)
    html = get_html_from_url(obj_url)
    obj_types = get_types_from_html(html)
    # interact with graph
    make_type_assertions_for_obj(conceptnet, obj_url, obj_types)

if __name__ == '__main__':
  main()

"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import graph
import urllib2

DBPEDIA_DATA_PREFIX = 'http://dbpedia.org/page/'
DBPEDIA_SOURCE = [u'source', u'web', u'dbpedia.org']
TYPE_RELATION = u'/rel/rdf/type'
TYPE_RELATION_PROP_KEY = u'owl:sameAs'
TYPE_RELATION_PROP_VAL = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'

def get_url_from_obj(obj_name):
  return DBPEDIA_DATA_PREFIX + obj_name

def get_html_from_url(url):
  page = urllib2.urlopen(url)
  html = page.read()
  page.close()
  return html

def get_types_from_html(html):
  types = []
  raw_list = html.split('<a class="uri" href="http://www.w3.org/1999/02/'
      '22-rdf-syntax-ns#type">', 1)[1].split('<ul>', 1)[1].split('</ul>', 1)[0]
  while 'href="' in raw_list:
    [new_type, raw_list] = raw_list.split('href="', 1)[1].split('">', 1)
    types.append(new_type)
  return types

def make_type_assertions_for_obj(obj_name):
  # get data from dbpedia
  url = get_url_from_obj(obj_name)
  html = get_html_from_url(url)
  types = get_types_from_html(html)
  # interact with graph
  concept = graph.get_or_create_node(url)
  relation = graph.get_or_create_relation(TYPE_RELATION)
  source = graph.get_or_create_source(DBPEDIA_SOURCE)
  relation[TYPE_RELATION_PROP_KEY] = TYPE_RELATION_PROP_VAL
  for type_url in types:
    type_concept = graph.get_or_create_node(type_url)
    assertion = get_or_create_assertion(TYPE_RELATION, url, type_url)
    graph.justify(source, assertion)

def main():
  obj_names = ['Tetris']
  for obj_name in obj_names:
    make_type_assertions_for_obj(obj_name)

if __name__ == '__main__':
  main()

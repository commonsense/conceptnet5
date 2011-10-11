"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize_topic, un_camel_case
import urllib
import urllib2

DBPEDIA_DATA_PREFIX = u'http://dbpedia.org/page/'
DBPEDIA_SOURCE = [u'source', u'web', u'dbpedia.org']
TYPE_HTML = ('<a class="uri" href="http://www.w3.org/1999/02/'
    '22-rdf-syntax-ns#type">')
TYPE_RELATION_NAME = u'InstanceOf'
WEB_TYPE_RELATION = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
TYPE_ASSERTION_PROPERTIES = {
    'source':u'dbpedia',
    'license':u'CC-By-SA',
    'normalized':'False'
}
NORM_ASSERTION_PROPERTIES = {
    'source':u'dbpedia',
    'license':u'CC-By-SA',
    'normalized':'False'
}
WIKIPEDIA_TITLES = 'breadth-first-articles.txt'

VERBOSE = True

def show_message(message):
  if VERBOSE:
    print message

def get_url_from_obj_name(obj_name):
  obj_url = DBPEDIA_DATA_PREFIX + urllib.quote(obj_name.encode('utf-8'))
  return obj_url

def get_html_from_url(url):
  page = urllib2.urlopen(url)
  html = page.read()
  page.close()
  return html

def normalize_topic_url(url):
    url = urllib.unquote(url).decode('utf-8', 'ignore')
    return normalize_topic(un_camel_case(url.strip('/').split('/')[-1]))

def get_types_from_html(html):
  if TYPE_HTML not in html:
    return []
  obj_types = []
  html = html.split(TYPE_HTML, 1)[1].split('<ul>', 1)[1].split('</ul>', 1)[0]
  while 'href="' in html:
    [obj_type, html] = html.split('href="', 1)[1].split('">', 1)
    if not 'owl#' in obj_type:
      obj_types.append(obj_type)
  return obj_types

def make_type_assertions_for_obj(conceptnet, obj_url, obj_types, source):
  concept = conceptnet.get_or_create_web_concept(urllib.unquote(obj_url))
  for obj_type in obj_types:
    obj_type_concept = conceptnet.get_or_create_web_concept(obj_type)
    assertion = conceptnet.get_or_create_assertion(
        WEB_TYPE_RELATION, [concept, obj_type_concept],
        properties=TYPE_ASSERTION_PROPERTIES)
    norm1 = conceptnet.get_or_create_concept('en', *normalize_topic_url(obj_url))
    norm2 = conceptnet.get_or_create_concept('en', *normalize_topic_url(obj_type))
    norm_assertion = conceptnet.get_or_create_assertion(
        '/relation/'+TYPE_RELATION_NAME, [norm1, norm2],
        properties=NORM_ASSERTION_PROPERTIES
    )
    conceptnet.justify(source, assertion)
    conceptnet.derive_normalized(assertion, norm_assertion)
    print assertion
    print norm_assertion

def main():
  wikipediaTitles = open(WIKIPEDIA_TITLES)
  conceptnet = JSONWriterGraph('json_data/dbpedia_data')
  source = conceptnet.get_or_create_source(DBPEDIA_SOURCE)
  conceptnet.justify('/', source)
  conceptnet.get_or_create_relation(WEB_TYPE_RELATION)
  conceptnet.get_or_create_relation(TYPE_RELATION_NAME)
  for line in wikipediaTitles:
    try:
      obj_name = line.strip().decode('utf-8')
    except Exception:
      show_message(u'WARNING: Could not decode \'%s\'.' % line)
      continue
    # get data from dbpedia
    obj_url = get_url_from_obj_name(obj_name)
    try:
      html = get_html_from_url(obj_url)
    except Exception:
      show_message(
          u'WARNING: Could not get DBPedia page for \'%s\'.' % obj_name)
      continue
    obj_types = get_types_from_html(html)
    # interact with graph
    make_type_assertions_for_obj(conceptnet, obj_url, obj_types, source)
  show_message(u'NOTICE: Script finished!')

if __name__ == '__main__':
  main()

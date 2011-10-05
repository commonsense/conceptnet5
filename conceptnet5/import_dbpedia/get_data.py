"""
Get data from DBPedia.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import urllib2

JUSTIFICATION = '/source/web/dbpedia.org'

def get_url_from_obj(obj_name):
  return 'http://dbpedia.org/page/%s' % obj_name

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

def main():
  obj_names = ['Tetris']
  for obj_name in obj_names:
    url = get_url_from_obj(obj_name)
    html = get_html_from_url(url)
    types = get_types_from_html(html)
    print types

if __name__ == '__main__':
  main()

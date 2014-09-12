# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.wiktparse.rules import EnWiktionarySemantics
from conceptnet5.util import get_support_data_filename
from nose.tools import eq_
import os


TESTDATA_DIR = get_support_data_filename("testdata")

def data_path(filename):
    return os.path.join(TESTDATA_DIR, filename)


ENTRY = {
 'site': 'en.wiktionary.org',
 'sections': [{'sections': [],
   'text': '*[[odečítat]]',
   'heading': 'Alternative forms'},
  {'sections': [{'sections': [],
     'text': '{{cs-conj-at|odčít}}',
     'heading': 'Conjugation'},
    {'sections': [], 'text': '* [[sčítat]]', 'heading': 'Antonyms'},
    {'sections': [],
     'text': '* [[odčítání]] {{g|n}}',
     'heading': 'Derived terms'}],
   'text': '{{cs-verb|a=i}}\n\n# to [[subtract]]',
   'heading': 'Verb'}],
 'title': 'odčítat',
 'language': 'Czech'
}

TARGET = [
 {'surfaceText': None,
  'id': '/e/596f54a5a692d232df21a5651a21ab9f3493fadf',
  'license': '/l/CC/By-SA',
  'source_uri': '/and/[/s/rule/definition_section/,/s/web/en.wiktionary.org/wiki/odčítat/]',
  'context': '/ctx/all',
  'dataset': '/d/wiktionary/en/cs',
  'sources': ['/s/rule/definition_section',
   '/s/web/en.wiktionary.org/wiki/odčítat'],
  'start': '/c/cs/odčítat/v',
  'uri': '/a/[/r/RelatedTo/,/c/cs/odčítat/v/,/c/en/subtract/]',
  'rel': '/r/RelatedTo',
  'features': ['/c/cs/odčítat/v /r/RelatedTo -',
   '/c/cs/odčítat/v - /c/en/subtract',
   '- /r/RelatedTo /c/en/subtract'],
  'weight': 1.0,
  'end': '/c/en/subtract'},
 {'surfaceText': None,
  'id': '/e/72d8bc56b9cbdc37bd8a6ae51ec07c0eb59f1429',
  'license': '/l/CC/By-SA',
  'source_uri': '/and/[/s/rule/link_section/,/s/web/en.wiktionary.org/wiki/odčítat/]',
  'context': '/ctx/all',
  'dataset': '/d/wiktionary/en/cs',
  'sources': ['/s/rule/link_section', '/s/web/en.wiktionary.org/wiki/odčítat'],
  'start': '/c/cs/odčítat/v',
  'uri': '/a/[/r/Antonym/,/c/cs/odčítat/v/,/c/cs/sčítat/]',
  'rel': '/r/Antonym',
  'features': ['/c/cs/odčítat/v /r/Antonym -',
   '/c/cs/odčítat/v - /c/cs/sčítat',
   '- /r/Antonym /c/cs/sčítat'],
  'weight': 1.0,
  'end': '/c/cs/sčítat'},
 {'surfaceText': None,
  'id': '/e/7f6174ccc58c40dc66a2698dbbd3d43c0df428ce',
  'license': '/l/CC/By-SA',
  'source_uri': '/and/[/s/rule/link_section/,/s/web/en.wiktionary.org/wiki/odčítat/]',
  'context': '/ctx/all',
  'dataset': '/d/wiktionary/en/cs',
  'sources': ['/s/rule/link_section', '/s/web/en.wiktionary.org/wiki/odčítat'],
  'start': '/c/cs/odčítání',
  'uri': '/a/[/r/DerivedFrom/,/c/cs/odčítání/,/c/cs/odčítat/v/]',
  'rel': '/r/DerivedFrom',
  'features': ['/c/cs/odčítání /r/DerivedFrom -',
   '/c/cs/odčítání - /c/cs/odčítat/v',
   '- /r/DerivedFrom /c/cs/odčítat/v'],
  'weight': 1.0,
  'end': '/c/cs/odčítat/v'}
]


def test_language_disambiguation():
    titledb = data_path('input/en_titles.db')
    semparser = EnWiktionarySemantics(titledb=titledb)
    eq_(semparser.parse_structured_entry(ENTRY), TARGET)

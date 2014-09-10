# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.util import get_support_data_filename
from conceptnet5.query import AssertionFinder
from conceptnet5.assoc_query import AssocSpaceWrapper
from conceptnet5.builders.index_assertions import index_assertions
from nose.tools import eq_
import os


TESTDATA_DIR = get_support_data_filename("testdata")
ASSERTIONS_DIR = os.path.join(TESTDATA_DIR, 'input/assertions')
ASSOC_DIR = os.path.join(TESTDATA_DIR, 'input/assoc_space')
DB_PATH = os.path.join(TESTDATA_DIR, 'output/assertions.db')
FINDER = None
SPANISH_EXAMPLE = '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]'


def setup():
    global FINDER
    index_assertions(ASSERTIONS_DIR, DB_PATH, input_shards=1, output_shards=1)
    FINDER = AssertionFinder(db_filename=DB_PATH, edge_dir=ASSERTIONS_DIR, nshards=1)


def teardown():
    os.unlink(DB_PATH + '.0')


def uris(assertions):
    return [a['uri'] for a in assertions]


def test_lookup():
    # Lookup by concept
    found = uris(FINDER.lookup('/c/en/example', limit=5))
    eq_(found,
        ['/a/[/r/RelatedTo/,/c/en/beauty/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/en/example/n/,/c/en/behaviour/]',
         '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fi/esikuva/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fro/essainple/n/,/c/en/example/]'])

    # Lookup by dataset
    found = uris(FINDER.lookup('/d/wiktionary/en/es'))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by exact assertion URI
    found = uris(FINDER.lookup(SPANISH_EXAMPLE))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by multiple criteria
    found = uris(FINDER.query({'start': '/c/ja', 'rel': '/r/TranslationOf', 'end': '/c/en/example'}, limit=3))
    print(found)
    eq_(found,
        ['/a/[/r/TranslationOf/,/c/ja/模範/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/例し/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/引き合い/,/c/en/example/]'])


def test_assoc():
    assoc = AssocSpaceWrapper(ASSOC_DIR, FINDER)
    results = assoc.associations([('/c/en/orange', 1.0)], limit=3)
    similar = [r[0] for r in results]
    eq_(similar, ['/c/en/orange', '/c/en/yellow', '/c/en/lemon'])

    results = assoc.associations([('/c/en/example', 1.0)], limit=3)
    similar = [r[0] for r in results]
    eq_(similar, ['/c/en/example', '/c/en/ideas', '/c/en/green'])

    results = assoc.associations([('/c/en/case_in_point/n', 1.0)], limit=3)
    similar = [r[0] for r in results]
    eq_(similar, ['/c/en/example', '/c/en/ideas', '/c/en/green'])

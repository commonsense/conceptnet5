from conceptnet5.util import get_support_data_filename
from conceptnet5.query import AssertionFinder
from conceptnet5.builders.index_assertions import index_assertions
from nose.tools import eq_
import os


TESTDATA_DIR = get_support_data_filename("testdata")
ASSERTIONS_DIR = os.path.join(TESTDATA_DIR, 'input/assertions')
DB_PATH = os.path.join(TESTDATA_DIR, 'output/assertions.db')
FINDER = None
SPANISH_EXAMPLE = '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]'


def setup():
    global FINDER
    index_assertions(ASSERTIONS_DIR, DB_PATH, shards=1, inputs=1)
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

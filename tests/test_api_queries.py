# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.util import get_support_data_filename
from conceptnet5.builders.index_assertions import index_assertions
from nose.tools import eq_
from conceptnet5.api import app, configure_api
import os
import json


TESTDATA_DIR = get_support_data_filename("testdata")
ASSERTIONS_DIR = os.path.join(TESTDATA_DIR, 'input/assertions')
DB_PATH = os.path.join(TESTDATA_DIR, 'output/assertions.db')
ASSOC_DIR = os.path.join(TESTDATA_DIR, 'input/assoc_space')
SPANISH_EXAMPLE = '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]'
CLIENT = None


def setup():
    global CLIENT
    index_assertions(ASSERTIONS_DIR, DB_PATH, input_shards=1, output_shards=1)
    configure_api(DB_PATH, ASSERTIONS_DIR, ASSOC_DIR, nshards=1)
    CLIENT = app.test_client()


def teardown():
    os.unlink(DB_PATH + '.0')


def uris(response):
    assertions = response['edges']
    return [a['uri'] for a in assertions]


def decode(response):
    return json.loads(response.data.decode('utf-8'))


def test_normalize():
    found = decode(CLIENT.get('/data/5.4/normalize?language=en&term=This%20is%20a%20test'))
    eq_(found, {'uri': '/c/en/this_be_test'})

    found = decode(CLIENT.get('/data/5.4/normalize?language=en&term=This_is_a_test'))
    eq_(found, {'uri': '/c/en/this_be_test'})

    found = decode(CLIENT.get('/data/5.4/normalize?language=es&term=Esto_es_una_PRUEBA'))
    eq_(found, {'uri': '/c/es/esto_es_una_prueba'})


def test_lookup():
    # Lookup by concept
    found = uris(decode(CLIENT.get('/data/5.4/c/en/example?limit=5')))
    eq_(found,
        ['/a/[/r/RelatedTo/,/c/en/beauty/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/en/example/n/,/c/en/behaviour/]',
         '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fi/esikuva/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fro/essainple/n/,/c/en/example/]'])

    # Lookup by dataset
    found = uris(decode(CLIENT.get('/data/5.4/d/wiktionary/en/es')))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by exact assertion URI
    found = uris(decode(CLIENT.get('/data/5.4' + SPANISH_EXAMPLE)))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by multiple criteria
    found = uris(decode(CLIENT.get(
        '/data/5.4/search?start=/c/ja&rel=/r/TranslationOf&end=/c/en/example&limit=3'
    )))
    print(found)
    eq_(found,
        ['/a/[/r/TranslationOf/,/c/ja/模範/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/例し/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/引き合い/,/c/en/example/]'])


def test_assoc():
    # Look up something that isn't in the assoc space, but can be associated
    # via the DB
    response = decode(CLIENT.get('/data/5.4/assoc/c/en/case_in_point?limit=3'))
    eq_(response['terms'], [['/c/en/case_in_point', 1.0]])
    similar = [item[0] for item in response['similar']]
    eq_(similar, ['/c/en/example', '/c/en/ideas', '/c/en/green'])

    # Look up something that gets no results
    response = decode(CLIENT.get('/data/5.4/assoc/c/zxx/gibberish'))
    similar = [item[0] for item in response['similar']]
    eq_(similar, [])

    # Look up a weighted list
    response = decode(CLIENT.get('/data/5.4/assoc/list/en/orange,red@-.5?limit=3'))
    eq_(response['terms'], [['/c/en/orange', 1.0], ['/c/en/red', -0.5]])
    similar = [item[0] for item in response['similar']]
    eq_(similar, ['/c/en/yellow', '/c/en/orange', '/c/en/lemon'])

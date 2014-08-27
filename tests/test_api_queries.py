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
SPANISH_EXAMPLE = '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]'
CLIENT = None

def setup():
    global CLIENT
    index_assertions(ASSERTIONS_DIR, DB_PATH, input_shards=1, output_shards=1)
    configure_api(DB_PATH, ASSERTIONS_DIR, nshards=1)
    CLIENT = app.test_client()


def teardown():
    os.unlink(DB_PATH + '.0')


def uris(response):
    assertions = response['edges']
    return [a['uri'] for a in assertions]


def decode(response):
    return json.loads(response.data.decode('utf-8'))


def test_lookup():
    # Lookup by concept
    found = uris(decode(CLIENT.get('/c/en/example?limit=5')))
    eq_(found,
        ['/a/[/r/RelatedTo/,/c/en/beauty/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/en/example/n/,/c/en/behaviour/]',
         '/a/[/r/RelatedTo/,/c/es/verbigracia/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fi/esikuva/n/,/c/en/example/]',
         '/a/[/r/RelatedTo/,/c/fro/essainple/n/,/c/en/example/]'])

    # Lookup by dataset
    found = uris(decode(CLIENT.get('/d/wiktionary/en/es')))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by exact assertion URI
    found = uris(decode(CLIENT.get(SPANISH_EXAMPLE)))
    eq_(found, [SPANISH_EXAMPLE])

    # Lookup by multiple criteria
    found = uris(decode(CLIENT.get(
        '/search?start=/c/ja&rel=/r/TranslationOf&end=/c/en/example&limit=3'
    )))
    print(found)
    eq_(found,
        ['/a/[/r/TranslationOf/,/c/ja/模範/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/例し/,/c/en/example/]',
         '/a/[/r/TranslationOf/,/c/ja/引き合い/,/c/en/example/]'])

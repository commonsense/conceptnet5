"""
This test can only be run when the full ConceptNet data has been built
(not just the test data). It confirms that
"""

from conceptnet5.util import get_data_filename
from conceptnet5.languages import CORE_LANGUAGES, COMMON_LANGUAGES, ALL_LANGUAGES
from conceptnet5.db.query import AssertionFinder

test_finder = None


def setUp():
    global test_finder
    test_finder = AssertionFinder('conceptnet-test')


def test_languages_exist():
    lang_stats_file = get_data_filename('stats/languages.txt')
    counts = {}
    for line in open(lang_stats_file, encoding='utf-8'):
        count_str, lang = line.strip().split()
        counts[lang] = int(count_str)

    for lang in ALL_LANGUAGES:
        assert lang in counts, lang

    for lang in COMMON_LANGUAGES:
        assert counts[lang] >= 1000, counts[lang]

    for lang in CORE_LANGUAGES:
        assert counts[lang] >= 100000, (lang, counts[lang])


def test_datasets_exist():
    for dataset in [
        '/d/conceptnet/4/en', '/d/conceptnet/4/pt', '/d/conceptnet/4/ja',
        '/d/conceptnet/4/zh', '/d/conceptnet/4/nl',
        '/d/dbpedia', '/d/jmdict', '/d/opencyc', '/d/verbosity', '/d/wordnet',
        '/d/wiktionary/en', '/d/wiktionary/fr', '/d/wiktionary/de'
    ]:
        # Test that each dataset has at least 100 assertions
        q = test_finder.query({'dataset': dataset}, limit=100)
        assert len(q) == 100, dataset

# Queries that all include the result "/r/Synonym/,/c/es/prueba/n/,/c/en/test/n/"
TEST_QUERIES = [
    {'node': '/c/en/test', 'other': '/c/es'},
    {'node': '/c/es', 'other': '/c/en/test'},
    {'start': '/c/es', 'end': '/c/en'},
    {'node': '/c/es/prueba/n'},
    {'node': '/c/es/prueba/n', 'source': '/s/resource/wordnet/rdf/3.1'},
    {'node': '/c/en/test', 'rel': '/r/Synonym', 'other': '/c/es/prueba'},
]
TEST_URI = "/a/[/r/Synonym/,/c/es/prueba/n/,/c/en/test/n/]"


def check_query(query):
    q = test_finder.query(query)
    q_uris = [match['@id'] for match in q]
    q_uris_set = set(q_uris)
    assert len(q_uris) == len(q_uris_set)
    assert TEST_URI in q_uris_set, q_uris_set


def test_queries():
    # Test that each of the above queries finds the expected assertion
    for query in TEST_QUERIES:
        yield check_query, query

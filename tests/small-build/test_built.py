"""
Test querying ConceptNet for information in the database that results from the
small test build.
"""

from conceptnet5.util import get_data_filename
from conceptnet5.languages import CORE_LANGUAGES, COMMON_LANGUAGES, ALL_LANGUAGES
from conceptnet5.db.query import AssertionFinder

test_finder = None


def setUp():
    global test_finder
    test_finder = AssertionFinder('conceptnet-test')


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

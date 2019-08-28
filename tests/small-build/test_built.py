"""
Test querying ConceptNet for information in the database that results from the
small test build.
"""

import subprocess
import pytest

from conceptnet5.db.query import AssertionFinder
from tests.conftest import run_build


@pytest.fixture
def test_finder():
    return AssertionFinder('conceptnet-test')


# Queries that all include the result "/r/Synonym/,/c/es/prueba/n/,/c/en/test/n/"
TEST_QUERIES = [
    {'node': '/c/en/test', 'other': '/c/es'},
    {'node': '/c/es', 'other': '/c/en/test'},
    {'start': '/c/es', 'end': '/c/en'},
    {'node': '/c/es/prueba/n'},
    {'node': '/c/es/prueba/n', 'source': '/s/resource/wordnet/rdf/3.1'},
    {'node': '/c/en/test', 'rel': '/r/Synonym', 'other': '/c/es/prueba'},
]
TEST_URI = "/a/[/r/Synonym/,/c/es/prueba/n/wn/act/,/c/en/test/n/wn/act/]"


@pytest.mark.parametrize('query', TEST_QUERIES)
def test_queries(test_finder, query):
    # Test that each of the above queries finds the expected assertion
    q = test_finder.query(query)
    q_uris = [match['@id'] for match in q]
    q_uris_set = set(q_uris)
    assert len(q_uris) == len(q_uris_set)
    assert TEST_URI in q_uris_set, q_uris_set


def _assert_result_dir_same_as_reference(result, reference):
    """
    Return True if all text files in result directory matched the text files in the
    reference directory and False otherwise. Skip the msgpack files.
    """
    cmd_args = ['diff', '-urN', '-x', '*.msgpack']

    # In Python 3.7, `stdout=subprocess.PIPE` can be replaced by the clearer
    # `capture_output=True`
    try:
        subprocess.run(
            cmd_args + [result, reference], stdout=subprocess.PIPE, check=True
        )
    except subprocess.CalledProcessError as err:
        print(err.output.decode('utf-8')[:10000])
        raise


def test_build_result(run_build):
    for subdir in ['assertions', 'assoc', 'edges']:
        result_dir = 'testdata/current/' + subdir
        reference_dir = 'testdata/reference/' + subdir
        _assert_result_dir_same_as_reference(result_dir, reference_dir)

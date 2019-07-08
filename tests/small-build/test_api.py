from conceptnet5 import api
from nose.tools import eq_


def test_related_query():
    # Test that we can look up related terms
    result = api.query_related('/c/en/test', limit=3)
    eq_(len(result['related']), 3)


def test_related_query_malformed():
    # Test that we fulfill a query for related terms to a nonsense URI, and
    # there are simply no results
    result = api.query_related('/c/en,test', limit=3)
    eq_(len(result['related']), 0)


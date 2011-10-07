from conceptnet5.graph import *

def test_normalize_uri():
    assert normalize_uri(' one two') == u'one_two'
    assert normalize_uri(normalize_uri(' one two')) == u'one_two'

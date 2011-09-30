from conceptnet5.graph import *

def test_lucene_escape():
    assert lucene_escape(u'one two') == ur'one\ two'
    assert lucene_escape(u'three') == ur'three'
    assert lucene_escape(u'^_^') == ur'\^_\^'
    assert lucene_escape(ur'\backslash') == ur'\\backslash'

def test_normalize_uri():
    assert normalize_uri(' one two') == u'one_two'
    assert normalize_uri(normalize_uri(' one two')) == u'one_two'

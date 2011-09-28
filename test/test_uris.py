from conceptnet5.graph import *

def test_safe_uris():
    assert uri_is_safe('test')
    assert uri_is_safe('foo/bar')
    assert not uri_is_safe(u'test')
    assert not uri_is_safe('foo:bar')
    assert uri_is_safe(encode_uri(u'test'))

def test_encoding():
    assert encode_uri(u'one two') == 'one_two'
    assert decode_uri('one_two') == u'one two'
    assert encode_uri(u'three:four') == 'three%3Afour'
    assert decode_uri('three%3Afour') == u'three:four'


from conceptnet5.language.lemmatize import lemmatize
from nose.tools import eq_


def test_lemmatize():
    eq_(lemmatize('en', 'eating'), ('eat', 'pres+ptcp'))
    eq_(lemmatize('en', 'carrots'), ('carrot', 'p'))
    eq_(lemmatize('en', 'is'), ('be', '3+s+pres'))
    eq_(lemmatize('en', 'good'), ('good', ''))
    eq_(lemmatize('es', 'tengo', 'v'), ('tener', '1+s+pres+ind'))

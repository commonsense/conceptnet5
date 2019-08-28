from conceptnet5.language.lemmatize import lemmatize
from conceptnet5.tests.conftest import run_build


def test_lemmatize(run_build):
    assert lemmatize('en', 'eating') == ('eat', 'pres+ptcp')
    assert lemmatize('en', 'carrots') == ('carrot', 'p')
    assert lemmatize('en', 'is') == ('be', '3+s+pres')
    assert lemmatize('en', 'good') == ('good', '')
    assert lemmatize('es', 'tengo', 'v') == ('tener', '1+s+pres+ind')

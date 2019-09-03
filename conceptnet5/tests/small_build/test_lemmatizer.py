import pytest

from conceptnet5.language.lemmatize import lemmatize
from conceptnet5.tests.conftest import run_build


LEMMA_EXAMPLES = [
    (('en', 'eating'), ('eat', 'pres+ptcp')),
    (('en', 'carrots'), ('carrot', 'p')),
    (('en', 'is'), ('be', '3+s+pres')),
    (('en', 'good'), ('good', '')),
    (('es', 'tengo', 'v'), ('tener', '1+s+pres+ind')),
]


@pytest.mark.parametrize('example', LEMMA_EXAMPLES)
def test_lemmatize(run_build, example):
    args, output = example
    assert lemmatize(*args) == output

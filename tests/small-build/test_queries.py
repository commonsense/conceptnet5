import pytest
from conceptnet5.db.query import AssertionFinder


@pytest.fixture
def test_finder():
    return AssertionFinder('conceptnet-test')


def test_lookup(test_finder):
    quiz1 = list(test_finder.lookup('/c/en/quiz'))
    assert len(quiz1) == 3

    quiz2 = list(test_finder.lookup('/c/en/quiz', offset=1))
    assert quiz2 == quiz1[1:]

    quiz3 = list(test_finder.lookup('/c/en/quiz', limit=1))
    assert quiz3 == quiz1[:1]

    verbosity_test = quiz1[0]
    assert verbosity_test['start']['@id'] == '/c/en/test'
    assert verbosity_test['end']['@id'] == '/c/en/quiz'
    assert verbosity_test['rel']['@id'] == '/r/RelatedTo'
    assert verbosity_test['@id'] == '/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]'
    assert verbosity_test['license'] == 'cc:by/4.0'
    source = verbosity_test['sources'][0]
    assert source['contributor'] == '/s/resource/verbosity'
    assert source['process'] == '/s/process/split_words'
    assert source['@id'] == '/and/[/s/process/split_words/,/s/resource/verbosity/]'


def test_lookup_dataset(test_finder):
    verbosity = list(test_finder.lookup('/d/verbosity'))
    assert len(verbosity) >= 2


def test_random_edges(test_finder):
    results = list(test_finder.random_edges(limit=10))
    assert len(results) == 10


def test_strip_control_chars(test_finder):
    assert test_finder.lookup('/c/en/test\x00') == test_finder.lookup('/c/en/test')
    assert not test_finder.lookup('/s/\x1a')


def get_query_ids(query, test_finder):
    return [match['@id'] for match in test_finder.query(query)]


def test_query_en_quiz(test_finder):
    q1 = get_query_ids({'start': '/c/en/test', 'end': '/c/en/quiz'}, test_finder)
    testquiz = {
        '/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]',
        '/a/[/r/Synonym/,/c/en/test/n/,/c/en/quiz/]',
        '/a/[/r/Synonym/,/c/en/test/n/wikt/en_1/,/c/en/quiz/]',
    }
    assert set(q1) == testquiz
    q2 = get_query_ids({'node': '/c/en/quiz'}, test_finder)
    assert set(q2) == testquiz

    q3 = get_query_ids({'node': '/c/en/test', 'other': '/c/en/quiz'}, test_finder)
    q4 = get_query_ids({'node': '/c/en/quiz', 'other': '/c/en/test'}, test_finder)
    assert set(q3) == testquiz
    assert set(q4) == testquiz


def test_query_en_form(test_finder):
    q = get_query_ids({'rel': '/r/FormOf', 'end': '/c/en/test'}, test_finder)
    assert q == ['/a/[/r/FormOf/,/c/en/tests/,/c/en/test/n/]']


def test_query_en_es(test_finder):
    q = get_query_ids({'start': '/c/en/test', 'end': '/c/es'}, test_finder)
    assert q == ['/a/[/r/Synonym/,/c/en/test/n/wikt/en_1/,/c/es/prueba/]']


def test_query_es(test_finder):
    q1 = get_query_ids({'node': '/c/es', 'rel': '/r/RelatedTo'}, test_finder)
    assert q1 == ['/a/[/r/RelatedTo/,/c/es/test/n/,/c/en/test/]']

    q2 = get_query_ids(
        {'start': '/c/es', 'end': '/c/es', 'rel': '/r/Synonym'}, test_finder
    )
    assert q2 == ['/a/[/r/Synonym/,/c/es/test/n/,/c/es/prueba/]']

    q3 = get_query_ids(
        {'node': '/c/es', 'other': '/c/es', 'rel': '/r/Synonym'}, test_finder
    )
    assert q3 == ['/a/[/r/Synonym/,/c/es/test/n/,/c/es/prueba/]']


def test_query_source(test_finder):
    q = get_query_ids(
        {'node': '/c/en/test', 'source': '/s/resource/jmdict/1.07'}, test_finder
    )
    assert q == ['/a/[/r/Synonym/,/c/ja/テスト/n/,/c/en/test/]']


def test_lookup_external(test_finder):
    found = list(test_finder.lookup('http://dbpedia.org/resource/Test_(assessment)'))
    assert len(found) == 1
    assert found[0]['start']['@id'] == '/c/en/test/n/wp/assessment'

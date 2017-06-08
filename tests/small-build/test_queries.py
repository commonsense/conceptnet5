from nose.tools import eq_
from conceptnet5.db.query import AssertionFinder

test_finder = None


def setUp():
    global test_finder
    test_finder = AssertionFinder('conceptnet-test')


def test_lookup():
    quiz1 = list(test_finder.lookup('/c/en/quiz'))
    eq_(len(quiz1), 2)

    quiz2 = list(test_finder.lookup('/c/en/quiz', offset=1))
    eq_(quiz2, quiz1[1:])

    quiz3 = list(test_finder.lookup('/c/en/quiz', limit=1))
    eq_(quiz3, quiz1[:1])

    verbosity_test = quiz1[0]
    eq_(verbosity_test['start']['@id'], '/c/en/test')
    eq_(verbosity_test['end']['@id'], '/c/en/quiz')
    eq_(verbosity_test['rel']['@id'], '/r/RelatedTo')
    eq_(verbosity_test['@id'], '/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]')
    eq_(verbosity_test['license'], 'cc:by/4.0')
    source = verbosity_test['sources'][0]
    eq_(source['contributor'], '/s/resource/verbosity')
    eq_(source['process'], '/s/process/split_words')
    eq_(source['@id'], '/and/[/s/process/split_words/,/s/resource/verbosity/]')


def get_query_ids(query):
    return [match['@id'] for match in test_finder.query(query)]


def test_query_en_quiz():
    q1 = get_query_ids({'start': '/c/en/test', 'end': '/c/en/quiz'})
    testquiz = [
        '/a/[/r/RelatedTo/,/c/en/test/,/c/en/quiz/]',
        '/a/[/r/Synonym/,/c/en/test/n/,/c/en/quiz/]',
    ]
    eq_(q1, testquiz)
    q2 = get_query_ids({'node': '/c/en/quiz'})
    eq_(q2, testquiz)

    q3 = get_query_ids({'node': '/c/en/test', 'other': '/c/en/quiz'})
    q4 = get_query_ids({'node': '/c/en/quiz', 'other': '/c/en/test'})
    eq_(q3, testquiz)
    eq_(q4, testquiz)


def test_query_en_form():
    q = get_query_ids({'rel': '/r/FormOf', 'end': '/c/en/test'})
    eq_(q, ['/a/[/r/FormOf/,/c/en/tests/,/c/en/test/n/]'])


def test_query_en_es():
    q = get_query_ids({'start': '/c/en/test', 'end': '/c/es'})
    eq_(q, ['/a/[/r/Synonym/,/c/en/test/n/,/c/es/prueba/]'])


def test_query_es():
    q1 = get_query_ids({'node': '/c/es', 'rel': '/r/RelatedTo'})
    eq_(q1, ['/a/[/r/RelatedTo/,/c/es/test/n/,/c/en/test/]'])

    q2 = get_query_ids({'start': '/c/es', 'end': '/c/es', 'rel': '/r/Synonym'})
    eq_(q2, ['/a/[/r/Synonym/,/c/es/test/n/,/c/es/prueba/]'])

    q3 = get_query_ids({'node': '/c/es', 'other': '/c/es', 'rel': '/r/Synonym'})
    eq_(q3, ['/a/[/r/Synonym/,/c/es/test/n/,/c/es/prueba/]'])


def test_query_source():
    q = get_query_ids({'node': '/c/en/test', 'source': '/s/resource/jmdict/1.07'})
    eq_(q, ['/a/[/r/Synonym/,/c/ja/テスト/n/,/c/en/test/]'])


def test_lookup_external():
    found = list(test_finder.lookup('http://dbpedia.org/resource/Test_(assessment)'))
    eq_(len(found), 1)
    eq_(found[0]['start']['@id'], '/c/en/test/n')

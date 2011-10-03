from conceptnet5.english_nlp import normalize

def test_normalize():
    assert normalize('this is a test') == 'this be test'
    
    # If we're using simplenlp, this will give "catherine havasus"; this is
    # one of the reasons to switch to using Morphy
    assert normalize('Catherine Havasi') == 'catherine havasi'

"""
Tools for working with English text.
"""
from .lemmatize import LEMMATIZER

STOPWORDS = [
    'the', 'a', 'an'
]

DROP_FIRST = ['to']


def english_filter(tokens):
    """
    Given a list of tokens, remove a small list of English stopwords.
    """
    non_stopwords = [token for token in tokens if token not in STOPWORDS]
    while non_stopwords and non_stopwords[0] in DROP_FIRST:
        non_stopwords = non_stopwords[1:]
    if non_stopwords:
        return non_stopwords
    else:
        return tokens


def english_lemmatized_filter(tokens):
    """
    Given a list of tokens, remove a small list of English stopwords, and
    reduce the words to their roots using a Wiktionary-based lemmatizer.
    """
    lemmas = [LEMMATIZER.lookup('en', tok)[0] for tok in tokens]
    return english_filter(lemmas)

"""
Tools for working with English text.
"""
from .lemmatize import LEMMATIZER

STOPWORDS = [
    'the', 'a', 'an', 'some', 'any',
    'you', 'me', 'him', 'it', 'them', 'i', 'we', 'she', 'he', 'they',
    'your', 'my', 'our', 'his', 'her', 'its', 'their', 'this', 'that',
    'these', 'those', 'something', 'someone', 'somebody', 'anything', 'anyone',
    "someone's", "something's", "anything's", "somebody's", "anyone's",
]


DROP_FIRST = ['to', 'be', 'is', 'are']


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

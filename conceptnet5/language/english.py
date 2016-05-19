"""
Tools for working with English text.
"""

STOPWORDS = ['the', 'a', 'an', 'some', 'any',
             'your', 'my', 'our', 'his', 'her', 'its', 'their', 'this', 'that',
             'these', 'those', 'something', 'someone', 'anything',
             'you', 'me', 'him', 'it', 'them', 'i', 'we', 'she', 'he', 'they']


DROP_FIRST = ['to', 'be']


def english_filter(tokens):
    """
    Given a list of tokens, remove a small list of English stopwords, and
    reduce the words to their WordNet roots using a simple lemmatizer.
    """
    non_stopwords = [token for token in tokens if token not in STOPWORDS]
    while non_stopwords and non_stopwords[0] in DROP_FIRST:
        non_stopwords = non_stopwords[1:]
    if non_stopwords:
        return non_stopwords
    else:
        return tokens

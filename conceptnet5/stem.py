from __future__ import unicode_literals
"""
This module contains stemmers, or more specifically lemmatizers, that reduce
words to a root form in a given language.

Currently, the only stemmer we use is Morphy, the built-in stemmer in WordNet,
which we apply to English concept names. Other languages are left alone.
"""
from metanl.nltk_morphy import normalize as normalize_english
from conceptnet5.uri import normalize_text, concept_uri


def stem_and_normalize(lang, text):
    """
    Make a normalized form of the given text in the given language. If the
    language is English, reduce words to their root form using metanl's
    implementation of Morphy. Otherwise, simply apply the function called
    `conceptnet5.uri.normalize_text`.
    
    >>> stem_and_normalize('en', 'this is a test')
    'this_be_test'
    >>> stem_and_normalize('es', 'ESTO ES UNA PRUEBA')
    'esto_es_una_prueba'
    """
    if lang == 'en':
        stem = normalize_english(text) or text
        return normalize_text(stem)
    else:
        return normalize_text(text)


def normalized_concept_uri(lang, text, *more):
    """
    Make the appropriate URI for a concept in a particular language, including
    stemming the text if necessary, normalizing it, and joining it into a
    concept URI.

    Items in 'more' will not be stemmed, but will go through the other
    normalization steps.

    >>> normalized_concept_uri('en', 'this is a test')
    '/c/en/this_be_test'
    >>> normalized_concept_uri('en', 'this is a test', 'n', 'example phrase')
    '/c/en/this_be_test/n/example_phrase'
    """
    norm_text = stem_and_normalize(lang, text)
    more_text = [normalize_text(item) for item in more]
    return concept_uri(lang, norm_text, *more_text)


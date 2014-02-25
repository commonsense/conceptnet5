from __future__ import unicode_literals
"""
This module contains stemmers, or more specifically lemmatizers, that reduce
words to a root form in a given language.

Currently, the only stemmer we use is Morphy, the built-in stemmer in WordNet,
which we apply to English concept names. Other languages are left alone.
"""
from metanl.nltk_morphy import normalize
from conceptnet5.uri import normalize_text


def stem_english(text):
    return normalize(text)


def stem_and_normalize(text, language):
    if language == 'en':
        return normalize_text(stem_english(text))
    else:
        return normalize_text(text)

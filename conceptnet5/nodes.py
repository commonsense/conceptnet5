from __future__ import unicode_literals
"""
This module constructs URIs for nodes (concepts) in various languages. This
puts the tools in conceptnet5.uri together with stemmers that reduce words
to a root form, providing a higher-level interface to looking things up in
ConceptNet.

Currently, the only stemmer we use is Morphy, the built-in stemmer in WordNet,
which we apply to English concept names. Other languages are left alone.

The advantage of using Morphy is that its intended output is WordNet 3 lemmas,
a well-established set of strings. Other stemmers present a moving target that
is harder to define.
"""

from conceptnet5.language.english import normalize as normalize_english
from conceptnet5.uri import normalize_text, concept_uri, split_uri, BAD_NAMES_FOR_THINGS

LCODE_ALIASES = {
    # Pretend that all Chinese languages and variants are equivalent. This is
    # linguistically problematic, but it's also very helpful for aligning them
    # on terms where they actually are the same.
    #
    # This would mostly be a problem if ConceptNet was being used to *generate*
    # Chinese natural language text, and I don't believe it is.
    'cmn': 'zh',
    'yue': 'zh',
    'nan': 'zh',
    'zh_TW': 'zh',
    'zh_CN': 'zh',

    # An easier case: consider Bahasa Indonesia and Bahasa Malay to be the
    # same language, with code 'ms', because they're already 90% the same.
    # Many sources use 'ms' to represent the entire macrolanguage, with
    # 'zsm' to refer to Bahasa Malay in particular.
    'zsm': 'ms',
    'id': 'ms'
}


def normalized_concept_name(lang, text):
    """
    Make a normalized form of the given text in the given language. If the
    language is English, reduce words to their root form using the tools in
    conceptnet5.language.english. Otherwise, simply apply the function called
    `conceptnet5.uri.normalize_text`.

    >>> normalized_concept_name('en', 'this is a test')
    'this_be_test'
    >>> normalized_concept_name('es', 'ESTO ES UNA PRUEBA')
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
    if lang in LCODE_ALIASES:
        lang = LCODE_ALIASES[lang]
    norm_text = normalized_concept_name(lang, text)
    more_text = [normalize_text(item) for item in more if item is not None]
    return concept_uri(lang, norm_text, *more_text)


def uri_to_lemmas(uri):
    """
    Given a normalized concept URI, extract the list of words (in their root
    form) that it contains in its text.

    >>> # This is the lemmatized concept meaning 'United States'
    >>> uri_to_lemmas('/c/en/unite_state')
    ['unite', 'state']
    >>> uri_to_lemmas('/c/en/township/n/united_states')
    ['township', 'unite', 'state']
    """
    uri_pieces = split_uri(uri)
    lemmas = uri_pieces[2].split('_')
    if len(uri_pieces) >= 5:
        lang = uri_pieces[1]
        text = uri_pieces[4].replace('_', ' ')
        if text not in BAD_NAMES_FOR_THINGS:
            disambig = normalized_concept_name(lang, text)
            lemmas.extend(disambig.split('_'))
    return lemmas


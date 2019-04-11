"""
This module constructs URIs for nodes (concepts) in various languages. This
puts the tools in conceptnet5.uri together with functions that normalize
terms and languages into a standard form (english_filter, simple_tokenize, LCODE_ALIASES).
"""

import re
from urllib.parse import urlparse

from conceptnet5.language.english import english_filter
from conceptnet5.languages import LCODE_ALIASES
from conceptnet5.uri import (
    concept_uri,
    get_uri_language,
    is_term,
    split_uri,
    uri_prefix,
    uri_to_label,
)
from wordfreq import simple_tokenize
from wordfreq.preprocess import preprocess_text


def preprocess_and_tokenize_text(lang, text):
    """
    Get a string made from the tokens in the text, joined by
    underscores.

    >>> preprocess_and_tokenize_text('en', ' cat')
    'cat'

    >>> preprocess_and_tokenize_text('en', 'Italian supercat')
    'italian_supercat'

    >>> preprocess_and_tokenize_text('en', 'a big dog')
    'a_big_dog'

    >>> preprocess_and_tokenize_text('en', 'Test?!')
    'test'

    >>> preprocess_and_tokenize_text('en', 'TEST.')
    'test'

    >>> preprocess_and_tokenize_text('en', 'test/test')
    'test_test'

    >>> preprocess_and_tokenize_text('de', '   u\N{COMBINING DIAERESIS}ber\\n')
    'über'

    >>> preprocess_and_tokenize_text('en', 'embedded' + chr(9) + 'tab')
    'embedded_tab'

    >>> preprocess_and_tokenize_text('en', '_')
    ''

    >>> preprocess_and_tokenize_text('en', ',')
    ''
    """
    text = preprocess_text(text.replace('_', ' '), lang)
    tokens = simple_tokenize(text)
    return '_'.join(tokens)


def topic_to_concept(language, topic):
    """
    Get a canonical representation of a Wikipedia topic, which may include
    a disambiguation string in parentheses. Returns a concept URI that
    may be disambiguated as a noun.

    >>> topic_to_concept('en', 'Township (United States)')
    '/c/en/township/n/wp/united_states'
    """
    # find titles of the form Foo (bar)
    topic = topic.replace('_', ' ')
    match = re.match(r'([^(]+) \(([^)]+)\)', topic)
    if not match:
        return standardized_concept_uri(language, topic)
    else:
        return standardized_concept_uri(
            language, match.group(1), 'n', 'wp', match.group(2)
        )


def standardized_concept_name(lang, text):
    raise NotImplementedError(
        "standardized_concept_name has been removed. "
        "Use preprocess_and_tokenize_text instead."
    )


normalized_concept_name = standardized_concept_name


def standardized_concept_uri(lang, text, *more):
    """
    Make the appropriate URI for a concept in a particular language, including
    removing English stopwords, normalizing the text in a way appropriate
    to that language (using the text normalization from wordfreq), and joining
    its tokens with underscores in a concept URI.

    This text normalization can smooth over some writing differences: for
    example, it removes vowel points from Arabic words, and it transliterates
    Serbian written in the Cyrillic alphabet to the Latin alphabet so that it
    can match other words written in Latin letters.

    'more' contains information to distinguish word senses, such as a part
    of speech or a WordNet domain. The items in 'more' get lowercased and
    joined with underscores, but skip many of the other steps -- for example,
    they won't have stopwords removed.

    >>> standardized_concept_uri('en', 'this is a test')
    '/c/en/this_is_test'
    >>> standardized_concept_uri('en', 'this is a test', 'n', 'example phrase')
    '/c/en/this_is_test/n/example_phrase'
    >>> standardized_concept_uri('sh', 'симетрија')
    '/c/sh/simetrija'
    """
    lang = lang.lower()
    if lang in LCODE_ALIASES:
        lang = LCODE_ALIASES[lang]
    if lang == 'en':
        token_filter = english_filter
    else:
        token_filter = None

    text = preprocess_text(text.replace('_', ' '), lang)
    tokens = simple_tokenize(text)
    if token_filter is not None:
        tokens = token_filter(tokens)
    norm_text = '_'.join(tokens)
    more_text = []
    for item in more:
        if item is not None:
            tokens = simple_tokenize(item.replace('_', ' '))
            if token_filter is not None:
                tokens = token_filter(tokens)
            more_text.append('_'.join(tokens))

    return concept_uri(lang, norm_text, *more_text)


normalized_concept_uri = standardized_concept_uri
standardize_concept_uri = standardized_concept_uri


def valid_concept_name(text):
    """
    Returns whether this text can be reasonably represented in a concept
    URI. This helps to protect against making useless concepts out of
    empty strings or punctuation.

    >>> valid_concept_name('word')
    True
    >>> valid_concept_name('the')
    True
    >>> valid_concept_name(',,')
    False
    >>> valid_concept_name(',')
    False
    >>> valid_concept_name('/')
    False
    >>> valid_concept_name(' ')
    False
    """
    tokens = simple_tokenize(text.replace('_', ' '))
    return len(tokens) > 0


def ld_node(uri, label=None):
    """
    Convert a ConceptNet URI into a dictionary suitable for Linked Data.
    """
    if label is None:
        label = uri_to_label(uri)
    ld = {'@id': uri, 'label': label}
    if is_term(uri):
        pieces = split_uri(uri)
        ld['language'] = get_uri_language(uri)

        # Get a reasonably-distinct sense label for the term.
        # Usually it will be the part of speech, but when we have fine-grained
        # information from Wikipedia or WordNet, it'll include the last
        # component as well.
        if len(pieces) > 3:
            ld['sense_label'] = pieces[3]

        if len(pieces) > 4 and pieces[4] in ('wp', 'wn'):
            ld['sense_label'] += ', ' + pieces[-1]

        ld['term'] = uri_prefix(uri)
        ld['@type'] = 'Node'
    elif uri.startswith('http'):
        domain = urlparse(uri).netloc
        ld['site'] = domain
        ld['term'] = uri

        # OpenCyc is down and UMBEL doesn't host their vocabulary on the
        # Web. This property indicates whether you can follow a link
        # via HTTP and retrieve more information.
        ld['site_available'] = domain not in {'sw.opencyc.org', 'umbel.org'}
        ld['@type'] = 'Node'
    elif uri.startswith('/r/'):
        ld['@type'] = 'Relation'
    return ld

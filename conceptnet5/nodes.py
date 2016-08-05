"""
This module constructs URIs for nodes (concepts) in various languages. This
puts the tools in conceptnet5.uri together with functions that normalize
terms and languages into a standard form.
"""

from conceptnet5.language.english import english_filter
from conceptnet5.language.token_utils import simple_tokenize
from conceptnet5.uri import concept_uri, split_uri, uri_prefix, parse_possible_compound_uri
from urllib.parse import urlparse
from .languages import LCODE_ALIASES
import re


def standardize_text(text, token_filter=None):
    """
    Get a string made from the tokens in the text, joined by
    underscores. The tokens may have a language-specific `token_filter`
    applied to them. See `standardize_as_list()`.

        >>> standardize_text(' cat')
        'cat'

        >>> standardize_text('a big dog', token_filter=english_filter)
        'big_dog'

        >>> standardize_text('Italian supercat')
        'italian_supercat'

        >>> standardize_text('a big dog')
        'a_big_dog'

        >>> standardize_text('a big dog', token_filter=english_filter)
        'big_dog'

        >>> standardize_text('to go', token_filter=english_filter)
        'go'

        >>> standardize_text('Test?!')
        'test'

        >>> standardize_text('TEST.')
        'test'

        >>> standardize_text('test/test')
        'test_test'

        >>> standardize_text('   u\N{COMBINING DIAERESIS}ber\\n')
        'über'

        >>> standardize_text('embedded' + chr(9) + 'tab')
        'embedded_tab'

        >>> standardize_text('_')
        ''

        >>> standardize_text(',')
        ''
    """
    tokens = simple_tokenize(text.replace('_', ' '))
    if token_filter is not None:
        tokens = token_filter(tokens)
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
        return standardized_concept_uri(language, match.group(1), 'n', 'wp', match.group(2))


def standardized_concept_name(lang, text):
    raise NotImplementedError(
        "standardized_concept_name has been removed. "
        "Use standardize_text instead."
    )

normalized_concept_name = standardized_concept_name


def standardized_concept_uri(lang, text, *more):
    """
    Make the appropriate URI for a concept in a particular language, including
    stemming the text if necessary, normalizing it, and joining it into a
    concept URI.

    Items in 'more' will not be stemmed, but will go through the other
    normalization steps.

    >>> standardized_concept_uri('en', 'this is a test')
    '/c/en/this_is_test'
    >>> standardized_concept_uri('en', 'this is a test', 'n', 'example phrase')
    '/c/en/this_is_test/n/example_phrase'
    """
    if lang == 'en':
        token_filter = english_filter
    else:
        token_filter = None
    lang = lang.lower()
    if lang in LCODE_ALIASES:
        lang = LCODE_ALIASES[lang]
    norm_text = standardize_text(text, token_filter)
    more_text = [standardize_text(item, token_filter) for item in more
                 if item is not None]
    return concept_uri(lang, norm_text, *more_text)

normalized_concept_uri = standardized_concept_uri
standardize_concept_uri = standardized_concept_uri


def get_uri_language(uri):
    """
    Extract the language from a concept URI. If the URI points to an assertion,
    get the language of its first concept.
    """
    if uri.startswith('/a/'):
        return get_uri_language(parse_possible_compound_uri('a', uri)[0])
    elif uri.startswith('/c/'):
        return split_uri(uri)[1]
    else:
        return None


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
    return bool(standardize_text(text))


def uri_to_label(uri):
    if uri.startswith('/c/'):
        uri = uri_prefix(uri)
    return uri.split('/')[-1].replace('_', ' ')


def ld_node(uri, label=None):
    """
    Convert a ConceptNet URI into a dictionary suitable for Linked Data.
    """
    if label is None:
        label = uri_to_label(uri)
    ld = {
        '@id': uri,
        'label': label
    }
    if uri.startswith('/c/'):
        pieces = split_uri(uri)
        ld['language'] = pieces[1]
        if len(pieces) > 3:
            ld['sense_label'] = '/'.join(pieces[3:])
        ld['term'] = uri_prefix(uri)
    elif uri.startswith('http'):
        domain = urlparse(uri).netloc
        ld['site'] = domain
        ld['term'] = uri
    return ld

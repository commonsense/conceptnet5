# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
"""
URIs are Unicode strings that represent the canonical name for any object in
ConceptNet. These can be used with the ConceptNet Web API, or referred to in a
Semantic Web application, by attaching the prefix:

    http://conceptnet5.media.mit.edu/data/VERSION

For example, the English concept "book" has the URI '/c/en/book'. This concept
can be referred to, or retrieved, using this complete URI (in version 5.2):

    http://conceptnet5.media.mit.edu/data/5.2/c/en/book
"""

import sys
import re
from ftfy import fix_text
from conceptnet5 import __version__ as VERSION

if sys.version_info.major >= 3:
    unicode = str

# All URIs are conceptually appended to this URL, when we need to interoperate
# with Semantic Web-style resources.
ROOT_URL = 'http://conceptnet5.media.mit.edu/data/%s' % VERSION

# If we end up trying to fit a piece of text that looks like these into a URI,
# it will mess up our patterns of URIs.
#
# To avoid having to raise an error, we'll represent all of these as a single
# underscore.
BAD_NAMES_FOR_THINGS = {'', ',', '[', ']', '/'}

# Whitespace should be replaced with underscores in URIs.
WHITESPACE_RE = re.compile('[\s]')


def normalize_text(text, lowercase=True):
    """
    When a piece of a URI is an arbitrary string, we standardize it in the
    following ways:

    - Ensure it is in Unicode, and standardize its Unicode representation
      with the `ftfy.fix_text` function.
    - Erase case distinctions by converting cased characters to lowercase.
    - Strip common punctuation, unless that would make the string empty.
    - Replace spaces with underscores.

    The result will be a Unicode string that can be used within a URI.

        >>> normalize_text(' cat')
        'cat'

        >>> normalize_text('Italian supercat')
        'italian_supercat'

        >>> normalize_text('Test?!')
        'test'

        >>> normalize_text('TEST.')
        'test'

        >>> normalize_text('test/test')
        'test_test'

        >>> normalize_text('   u\N{COMBINING DIAERESIS}ber\\n')
        'über'

        >>> normalize_text('embedded' + chr(9) + 'tab')
        'embedded_tab'

        >>> normalize_text(',')
        '_'
    """
    if not isinstance(text, unicode):
        raise ValueError("All texts must be Unicode, not bytes.")

    # Replace slashes with spaces, which will become underscores later.
    # Slashes should separate pieces of a URI, and shouldn't appear within
    # a piece.
    text = fix_text(text, normalization='NFC').strip()

    # Represent texts that break our URI representation as a single
    # underscore.
    if text in BAD_NAMES_FOR_THINGS:
        return '_'

    text = text.replace('/', ' ')
    text = text.strip('.,?!"') or text
    if lowercase:
        text = text.lower()
    text = WHITESPACE_RE.sub('_', text)
    return text


def valid_concept_name(text):
    """
    Returns whether this text can be reasonably represented in a concept
    URI. This helps to protect against making useless concepts out of
    empty strings or punctuation.

    >>> valid_concept_name('word')
    True
    >>> valid_concept_name(',,')
    True
    >>> valid_concept_name(',')
    False
    >>> valid_concept_name('/')
    False
    >>> valid_concept_name(' ')
    False
    """
    if normalize_text(text) == '_':
        return False
    else:
        return True


def join_uri(*pieces):
    """
    `join_uri` builds a URI from constituent pieces that should be joined
    with slashes (/).

    Leading and trailing on the pieces are acceptable, but will be ignored.
    The resulting URI will always begin with a slash and have its pieces
    separated by a single slash.

    The pieces do not have `normalize_text` applied to them; to make sure your
    URIs are in normal form, run `normalize_text` on each piece that represents
    arbitrary text.

    >>> join_uri('/c', 'en', 'cat')
    '/c/en/cat'

    >>> join_uri('c', 'en', ' spaces ')
    '/c/en/ spaces '

    >>> join_uri('/r/', 'AtLocation/')
    '/r/AtLocation'

    >>> join_uri('/test')
    '/test'

    >>> join_uri('test')
    '/test'

    >>> join_uri('/test', '/more/')
    '/test/more'
    """
    joined = '/' + ('/'.join([piece.strip('/') for piece in pieces]))
    return joined


def concept_uri(lang, text, pos=None, disambiguation=None):
    """
    `concept_uri` builds a representation of a concept, which is a word or
    phrase of a particular language, which can participate in relations with
    other concepts, and may be linked to concepts in other languages.

    Every concept has an ISO language code and a text. It may also have a part
    of speech (pos), which is typically a single letter. If it does, it may
    have a disambiguation, a string that distinguishes it from other concepts
    with the same text.

    `text` and `disambiguation` should be strings that have already been run
    through `normalize_text`.

    This is a low-level interface. See `normalized_concept_uri` in nodes.py for
    a more generally applicable function that also deals with special
    per-language handling.

    >>> concept_uri('en', 'cat')
    '/c/en/cat'
    >>> concept_uri('en', 'cat', 'n')
    '/c/en/cat/n'
    >>> concept_uri('en', 'cat', 'n', 'feline')
    '/c/en/cat/n/feline'
    >>> concept_uri('en', 'this is wrong')
    Traceback (most recent call last):
        ...
    AssertionError: 'this is wrong' is not in normalized form
    """
    assert text == normalize_text(text), "%r is not in normalized form" % text
    if pos is None:
        if disambiguation is not None:
            raise ValueError("Disambiguated concepts must have a part of speech")
        return join_uri('/c', lang, text)
    else:
        if disambiguation is None:
            return join_uri('/c', lang, text, pos)
        else:
            assert disambiguation == normalize_text(disambiguation),\
                "%r is not in normalized form" % disambiguation
            return join_uri('/c', lang, text, pos, disambiguation)


def compound_uri(op, args):
    """
    Some URIs represent a compound structure or operator built out of a number
    of arguments. Some examples are the '/and' and '/or' operators, which
    represent a conjunction or disjunction over two or more URIs, which may
    themselves be compound URIs; or the assertion structure, '/a', which takes
    a relation and two URIs as its arguments.

    This function takes the main 'operator', with the slash included, and an
    arbitrary number of arguments, and produces the URI that represents the
    entire compound structure.

    These structures contain square brackets as segments, which look like
    `/[/` and `/]/`, so that compound URIs can contain other compound URIs
    without ambiguity.

    >>> compound_uri('/nothing', [])
    '/nothing/[/]'
    >>> compound_uri('/a', ['/r/CapableOf', '/c/en/cat', '/c/en/sleep'])
    '/a/[/r/CapableOf/,/c/en/cat/,/c/en/sleep/]'
    """
    items = [op]
    first_item = True
    items.append('[')
    for arg in args:
        if first_item:
            first_item = False
        else:
            items.append(',')
        items.append(arg)
    items.append(']')
    return join_uri(*items)


def split_uri(uri):
    """
    Get the slash-delimited pieces of a URI.

    >>> split_uri('/c/en/cat/n/feline')
    ['c', 'en', 'cat', 'n', 'feline']
    >>> split_uri('/')
    []
    """
    uri2 = uri.lstrip('/')
    if not uri2:
        return []
    return uri2.split('/')


def uri_prefixes(uri, min_pieces=2):
    """
    Get URIs that are prefixes of a given URI: that is, they begin with the
    same path components. By default, the prefix must have at least 2
    components.

    If the URI has sub-parts that are grouped by square brackets, then
    only complete sub-parts will be allowed in prefixes.

    >>> list(uri_prefixes('/c/en/cat/n/feline'))
    ['/c/en', '/c/en/cat', '/c/en/cat/n', '/c/en/cat/n/feline']
    >>> list(uri_prefixes('/test/[/group/one/]/[/group/two/]'))
    ['/test/[/group/one/]', '/test/[/group/one/]/[/group/two/]']
    """
    pieces = []
    for piece in split_uri(uri):
        pieces.append(piece)
        if len(pieces) >= min_pieces:
            if pieces.count('[') == pieces.count(']'):
                yield join_uri(*pieces)


def parse_compound_uri(uri):
    """
    Given a compound URI, extract its operator and its list of arguments.

    >>> parse_compound_uri('/nothing/[/]')
    ('/nothing', [])
    >>> parse_compound_uri('/a/[/r/CapableOf/,/c/en/cat/,/c/en/sleep/]')
    ('/a', ['/r/CapableOf', '/c/en/cat', '/c/en/sleep'])
    >>> parse_compound_uri('/or/[/and/[/s/one/,/s/two/]/,/and/[/s/three/,/s/four/]/]')
    ('/or', ['/and/[/s/one/,/s/two/]', '/and/[/s/three/,/s/four/]'])
    """
    pieces = split_uri(uri)
    if pieces[-1] != ']':
        raise ValueError("Compound URIs must end with /]")
    if '[' not in pieces:
        raise ValueError("Compound URIs must contain /[/ at the beginning of "
                         "the argument list")
    list_start = pieces.index('[')
    op = join_uri(*pieces[:list_start])

    chunks = []
    current = []
    depth = 0

    # Split on commas, but not if they're within additional pairs of brackets.
    for piece in pieces[(list_start + 1):-1]:
        if piece == ',' and depth == 0:
            chunks.append('/' + ('/'.join(current)).strip('/'))
            current = []
        else:
            current.append(piece)
            if piece == '[':
                depth += 1
            elif piece == ']':
                depth -= 1

    assert depth == 0, "Unmatched brackets in %r" % uri
    if current:
        chunks.append('/' + ('/'.join(current)).strip('/'))
    return op, chunks


def parse_possible_compound_uri(op, uri):
    """
    The AND and OR conjunctions can be expressed as compound URIs, but if they
    contain only one thing, they are returned as just that single URI, not a
    compound.

    This function returns the list of things in the compound URI if its operator
    matches `op`, or a list containing the URI itself if not.

    >>> parse_possible_compound_uri(
    ...    'or', '/or/[/and/[/s/one/,/s/two/]/,/and/[/s/three/,/s/four/]/]'
    ... )
    ['/and/[/s/one/,/s/two/]', '/and/[/s/three/,/s/four/]']
    >>> parse_possible_compound_uri('or', '/s/contributor/omcs/dev')
    ['/s/contributor/omcs/dev']
    """
    if uri.startswith('/' + op + '/'):
        return parse_compound_uri(uri)[1]
    else:
        return [uri]


def conjunction_uri(*sources):
    """
    Make a URI representing a conjunction of sources that work together to provide
    an assertion. The sources will be sorted in lexicographic order.

    >>> conjunction_uri('/s/contributor/omcs/dev')
    '/s/contributor/omcs/dev'

    >>> conjunction_uri('/s/rule/some_kind_of_parser', '/s/contributor/omcs/dev')
    '/and/[/s/contributor/omcs/dev/,/s/rule/some_kind_of_parser/]'
    """
    if len(sources) == 0:
        # Logically, a conjunction with 0 inputs represents 'True', a
        # proposition that cannot be denied. This could be useful as a
        # justification for, say, mathematical axioms, but when it comes to
        # ConceptNet, that kind of thing makes us uncomfortable and shouldn't
        # appear in the data.
        raise ValueError("Conjunctions of 0 things are not allowed")
    elif len(sources) == 1:
        return sources[0]
    else:
        return compound_uri('/and', sorted(set(sources)))


def disjunction_uri(*sources):
    """
    Make a URI representing a choice of sources that provide the same assertion. The
    sources will be sorted in lexicographic order.

    >>> disjunction_uri('/s/contributor/omcs/dev')
    '/s/contributor/omcs/dev'

    >>> disjunction_uri('/s/contributor/omcs/rspeer', '/s/contributor/omcs/dev')
    '/or/[/s/contributor/omcs/dev/,/s/contributor/omcs/rspeer/]'
    """
    if len(sources) == 0:
        # If something has a disjunction of 0 sources, we have no reason to
        # believe it, and therefore it shouldn't be here.
        raise ValueError("Disjunctions of 0 things are not allowed")
    elif len(sources) == 1:
        return sources[0]
    else:
        return compound_uri('/or', sorted(set(sources)))


def assertion_uri(rel, *args):
    """
    Make a URI for an assertion.

    There will usually be two items in *args, the 'start' and 'end' of the
    assertion. However, this can support relations with different number
    of arguments.

    >>> assertion_uri('/r/CapableOf', '/c/en/cat', '/c/en/sleep')
    '/a/[/r/CapableOf/,/c/en/cat/,/c/en/sleep/]'
    """
    assert rel.startswith('/r')
    return compound_uri('/a', (rel,) + args)


def and_or_tree(list_of_lists):
    """
    An and-or tree represents a disjunction of conjunctions. In ConceptNet terms,
    it represents all the reasons we might believe a particular assertion.

    >>> and_or_tree([['/s/one', '/s/two'], ['/s/three', '/s/four']])
    '/or/[/and/[/s/four/,/s/three/]/,/and/[/s/one/,/s/two/]/]'
    """
    conjunctions = [conjunction_uri(*sublist) for sublist in list_of_lists]
    return disjunction_uri(*conjunctions)


class Licenses(object):
    cc_attribution = '/l/CC/By'
    cc_sharealike = '/l/CC/By-SA'

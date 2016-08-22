"""
URIs are Unicode strings that represent the canonical name for any object in
ConceptNet. These can be used with the ConceptNet Web API, or referred to in a
Semantic Web application, by attaching the prefix:

    http://api.conceptnet.io

For example, the English concept "book" has the URI '/c/en/book'. This concept
can be referred to, or retrieved, using this complete URI:

    http://api.conceptnet.io/c/en/book
"""


def standardize_text(text, lowercase=True):
    raise NotImplementedError(
        "This function has been superseded by "
        "conceptnet5.nodes.standardize_text."
    )


def join_uri(*pieces):
    """
    `join_uri` builds a URI from constituent pieces that should be joined
    with slashes (/).

    Leading and trailing on the pieces are acceptable, but will be ignored.
    The resulting URI will always begin with a slash and have its pieces
    separated by a single slash.

    The pieces do not have `standardize_text` applied to them; to make sure your
    URIs are in normal form, run `standardize_text` on each piece that represents
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


def concept_uri(lang, text, *more):
    """
    `concept_uri` builds a representation of a concept, which is a word or
    phrase of a particular language, which can participate in relations with
    other concepts, and may be linked to concepts in other languages.

    Every concept has an ISO language code and a text. It may also have a part
    of speech (pos), which is typically a single letter. If it does, it may
    have a disambiguation, a string that distinguishes it from other concepts
    with the same text.

    This function should be called as follows, where arguments after `text`
    are optional:

        concept_uri(lang, text, pos, disambiguation...)

    `text` and `disambiguation` should be strings that have already been run
    through `standardize_text`.

    This is a low-level interface. See `standardized_concept_uri` in nodes.py for
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
    assert ' ' not in text, "%r is not in normalized form" % text
    if len(more) > 0:
        if len(more[0]) != 1:
            # We misparsed a part of speech; everything after the text is
            # probably junk
            more = []
        for dis1 in more[1:]:
            assert ' ' not in dis1,\
                "%r is not in normalized form" % dis1

    return join_uri('/c', lang, text, *more)


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

    >>> split_uri('/c/en/cat/n/animal')
    ['c', 'en', 'cat', 'n', 'animal']
    >>> split_uri('/')
    []
    """
    if not uri.startswith('/'):
        return [uri]
    uri2 = uri.lstrip('/')
    if not uri2:
        return []
    return uri2.split('/')


def uri_prefix(uri, max_pieces=3):
    """
    Strip off components that might make a ConceptNet URI too detailed. Only
    the first `max_pieces` components will be kept.

    By default, `max_pieces` is 3, making this function useful for converting
    disambiguated concepts into their more general ambiguous forms.

    If the URI is actually a fully qualified URL, no components are removed.

    >>> uri_prefix('/c/en/cat/n/animal')
    '/c/en/cat'
    >>> uri_prefix('/c/en/cat/n')
    '/c/en/cat'
    >>> uri_prefix('/c/en/cat')
    '/c/en/cat'
    >>> uri_prefix('/c/en')
    '/c/en'
    >>> uri_prefix('/c/en/cat', 2)
    '/c/en'
    >>> uri_prefix('http://en.wikipedia.org/wiki/Example')
    'http://en.wikipedia.org/wiki/Example'
    """
    if is_absolute_url(uri):
        return uri
    pieces = split_uri(uri)[:max_pieces]
    return join_uri(*pieces)


def uri_prefixes(uri, min_pieces=2):
    """
    Get URIs that are prefixes of a given URI: that is, they begin with the
    same path components. By default, the prefix must have at least 2
    components.

    If the URI has sub-parts that are grouped by square brackets, then
    only complete sub-parts will be allowed in prefixes.

    >>> list(uri_prefixes('/c/en/cat/n/animal'))
    ['/c/en', '/c/en/cat', '/c/en/cat/n', '/c/en/cat/n/animal']
    >>> list(uri_prefixes('/test/[/group/one/]/[/group/two/]'))
    ['/test/[/group/one/]', '/test/[/group/one/]/[/group/two/]']
    >>> list(uri_prefixes('http://en.wikipedia.org/wiki/Example'))
    ['http://en.wikipedia.org/wiki/Example']
    """
    if is_absolute_url(uri):
        yield uri
        return
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


def assertion_uri(rel, start, end):
    """
    Make a URI for an assertion, as a compound URI of its relation, start node,
    and end node.

    >>> assertion_uri('/r/CapableOf', '/c/en/cat', '/c/en/sleep')
    '/a/[/r/CapableOf/,/c/en/cat/,/c/en/sleep/]'
    """
    assert rel.startswith('/r'), rel
    return compound_uri('/a', (rel, start, end))


def is_concept(uri):
    return uri.startswith('/c/')


def is_absolute_url(uri):
    # We have URLs pointing to Creative Commons licenses, starting with 'cc:',
    # which for Linked Data purposes are absolute URLs because they'll be
    # resolved into full URLs.
    return uri.startswith('http') or uri.startswith('cc:')


class Licenses:
    cc_attribution = 'cc:by/4.0'
    cc_sharealike = 'cc:by-sa/4.0'

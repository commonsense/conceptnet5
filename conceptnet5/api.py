"""
This file defines the ConceptNet web API responses.
"""

from conceptnet5.nodes import ld_node, standardized_concept_uri
from conceptnet5.vectors.query import VectorSpaceWrapper

VECTORS = VectorSpaceWrapper()
FINDER = VECTORS.finder
CONTEXT = ["http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json"]
VALID_KEYS = ['rel', 'start', 'end', 'node', 'other', 'source', 'uri']


def success(response):
    response['@context'] = CONTEXT
    return response


def error(response, status, details):
    response['@context'] = CONTEXT
    response['error'] = {'status': status, 'details': details}
    return response


def make_query_url(url, items):
    """
    Take a URL base and a list of key/value pairs representing parameters,
    and convert them to a complete URL with those parameters in the query
    string.
    """
    str_items = ['{}={}'.format(*item) for item in items]
    if not str_items:
        return url
    else:
        return url + '?' + ('&'.join(str_items))


def groupkey_to_pairs(groupkey, term):
    """
    Convert a 'groupkey', a structure defined below in 'lookup_grouped_by_feature',
    to a list of pairs representing the parameters that query for just the
    edges in that feature group.
    """
    direction, rel = groupkey
    if direction == 1:
        return [('rel', rel), ('start', term)]
    elif direction == -1:
        return [('rel', rel), ('end', term)]
    else:
        return [('rel', rel), ('node', term)]


def paginated_url(url, params, offset, limit):
    """
    Take in a URL and set 'offset=' and 'limit=' parameters on its query string,
    replacing those parameters if they already existed.
    """
    new_params = [
        (key, val) for (key, val) in params if key != 'offset' and key != 'limit'
    ] + [('offset', offset), ('limit', limit)]
    return make_query_url(url, new_params)


def make_paginated_view(url, params, offset, limit, more):
    """
    Create a JSON-LD structure that describes the fact that this is just
    one page of results and more pages exist.

    This follows what used to be the recommendation at
    https://www.w3.org/community/hydra/wiki/Pagination. It now sort of resembles
    the "PartialCollectionView" proposal. This stuff is still not
    well-standardized.
    """
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit
    pager = {
        '@id': paginated_url(url, params, offset, limit),
        '@type': 'PartialCollectionView',
        'firstPage': paginated_url(url, params, 0, limit),
        'paginatedProperty': 'edges',
    }
    if offset > 0:
        pager['previousPage'] = paginated_url(url, params, prev_offset, limit)
    if more:
        pager['nextPage'] = paginated_url(url, params, next_offset, limit)
        pager['comment'] = (
            "There are more results. Follow the 'nextPage' link for more."
        )
    return pager


def lookup_grouped_by_feature(term, filters=None, feature_limit=10):
    """
    Given a query for a concept, return assertions about that concept grouped by
    their features (for example, "A dog wants to ..." could be a group).
    """
    if not term.startswith('/c/'):
        return error(
            {}, 400, 'Only concept nodes (starting with /c/) can be grouped by feature.'
        )

    found = FINDER.lookup_grouped_by_feature(term, limit=(feature_limit + 1))
    grouped = []
    for groupkey, assertions in found.items():
        direction, rel = groupkey
        base_url = '/query'
        feature_pairs = groupkey_to_pairs(groupkey, term)
        url = make_query_url(base_url, feature_pairs)
        symmetric = direction == 0
        group = {
            '@id': url,
            'weight': sum(assertion['weight'] for assertion in assertions),
            'feature': dict(feature_pairs),
            'edges': assertions[:feature_limit],
            'symmetric': symmetric,
        }
        if len(assertions) > feature_limit:
            view = make_paginated_view(
                base_url, feature_pairs, 0, feature_limit, more=True
            )
            group['view'] = view

        grouped.append(group)

    grouped.sort(key=lambda g: -g['weight'])
    for group in grouped:
        del group['weight']

    response = ld_node(term)
    if not grouped and not filters:
        return error(
            response, 404, '%r is not a node in ConceptNet.' % response['label']
        )
    else:
        response['features'] = grouped
        return success(response)


def lookup_paginated(term, limit=50, offset=0):
    """
    Look up edges associated with a particular URI, and return a paginated,
    flat list of results.
    """
    # Query one more edge than asked for, so we know if there are more
    found = FINDER.lookup(term, limit=(limit + 1), offset=offset)
    edges = found[:limit]
    response = {'@id': term, 'edges': edges}
    more = len(found) > len(edges)
    if len(found) > len(edges) or offset != 0:
        response['view'] = make_paginated_view(term, (), offset, limit, more=more)
    if not found:
        return error(response, 404, '%r is not a node in ConceptNet.' % term)
    else:
        return success(response)


def lookup_single_assertion(uri):
    """
    Look up an edge with a particular URI (starting with /a/). This differs
    from `lookup_paginated` because there will be at most one matching edge.
    We return that edge if it exists, and if not, we return a 404 error.
    """
    found = FINDER.lookup(uri, limit=1)
    response = {'@id': uri}
    if not found:
        return error(response, 404, '%r is not an assertion in ConceptNet.' % uri)
    else:
        response.update(found[0])
        return success(response)


def query_relatedness(node1, node2):
    """
    Query for the similarity between node1 and node2. Return the cosine
    similarity between the vectors of these two terms.
    """
    if node1 is None or node2 is None:
        return error({}, 400, 'Arguments should be called node1 and node2.')

    url = make_query_url('/relatedness', [('node1', node1), ('node2', node2)])
    try:
        relatedness = VECTORS.get_similarity(node1, node2)
        response = {'@id': url, 'value': round(float(relatedness), 3)}
        return success(response)
    except ValueError:
        return error(
            {'@id': url},
            400,
            "Couldn't look up {} or {} (or both).".format(repr(node1), repr(node2)),
        )


# TODO: document querying for a list of terms
def query_related(uri, filter=None, limit=20):
    """
    Query for terms that are related to a term, or list of terms, according
    to the mini version of ConceptNet Numberbatch.
    """
    if uri.startswith('/c/'):
        query = uri
    elif uri.startswith('/list/') and uri.count('/') >= 3:
        try:
            _, _list, language, termlist = uri.split('/', 3)
            query = []
            term_pieces = termlist.split(',')
            for piece in term_pieces:
                if '@' in piece:
                    term, weight = piece.split('@')
                    weight = float(weight)
                else:
                    term = piece
                    weight = 1.
                query.append(('/c/{}/{}'.format(language, term), weight))
        except ValueError:
            return error({'@id': uri}, 400, "Couldn't parse this term list: %r" % uri)
    else:
        return error(
            {'@id': uri},
            404,
            '%r is not something that I can find related terms to.' % uri,
        )

    found = VECTORS.similar_terms(query, filter=filter, limit=limit)
    related = [
        {'@id': key, 'weight': round(float(weight), 3)}
        for (key, weight) in found.items()
    ]
    response = {'@id': uri, 'related': related}
    return response


def query_paginated(query, offset=0, limit=50):
    """
    Search ConceptNet for edges matching a query.

    The query should be provided as a dictionary of criteria. The `query`
    function in the `.api` module constructs such a dictionary.
    """
    found = FINDER.query(query, limit=limit + 1, offset=offset)
    edges = found[:limit]
    response = {'@id': make_query_url('/query', query.items()), 'edges': edges}
    more = len(found) > len(edges)
    if len(found) > len(edges) or offset != 0:
        response['view'] = make_paginated_view(
            '/query', sorted(query.items()), offset, limit, more=more
        )
    return success(response)


def standardize_uri(language, text):
    """
    Look up the URI for a given piece of text.
    """
    if text is None or language is None:
        return error(
            {}, 400, "You should include the 'text' and 'language' parameters."
        )

    text = text.replace('_', ' ')
    uri = standardized_concept_uri(language, text)
    response = {'@id': uri}
    return success(response)

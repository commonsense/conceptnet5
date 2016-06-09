from conceptnet5.uri import uri_prefix
from conceptnet5.edges import transform_for_linked_data
from conceptnet5.util import get_data_filename
from conceptnet5.formats.msgpack_stream import read_msgpack_value
from conceptnet5.hashtable.index import HashTableIndex
from conceptnet5.relations import SYMMETRIC_RELATIONS
from collections import defaultdict


VALID_KEYS = {
    'rel', 'start', 'end', 'node', 'dataset', 'license', 'sources',
    'surfaceText', 'uri'
}
INDEXED_KEYS = {
    'rel', 'start', 'end', 'node', 'dataset', 'sources',
    'surfaceText', 'uri'
}


def field_match(matchable, query):
    """
    Determines whether a given field of an edge (or, in particular, an
    assertion) matches the given query.

    If the query is a URI, it will match prefixes of longer URIs, unless
    `/.` is added to the end of the query.

    For example, `/c/en/dog` will match assertions about `/c/en/dog/n/animal`,
    but `/c/en/dog/.` will only match assertions about `/c/en/dog`.
    """
    query = query.rstrip('/')
    if isinstance(matchable, list):
        return any(field_match(subval, query) for subval in matchable)
    elif isinstance(matchable, dict):
        return any(field_match(subval, query) for subval in matchable.values())
    elif query.endswith('/.'):
        return matchable == query[:-2]
    else:
        return (matchable[:len(query)] == query and
                (len(matchable) == len(query) or matchable[len(query)] == '/'))


def groupkey_to_features(groupkey):
    groupdict = dict(groupkey)
    if 'node' in groupdict:
        return ['{} {} -'.format(groupdict['node'], groupdict['rel']),
                '- {} {}'.format(groupdict['rel'], groupdict['node'])]
    else:
        feat = '{} {} {}'.format(
            groupdict.get('start', '-'),
            groupdict.get('rel', '-'),
            groupdict.get('end', '-')
        )
        return [feat]


def groupkey_to_query(groupkey):
    params = ['{}={}'.format(key, val) for key, val in groupkey]
    return '&'.join(params)


def make_paginated_view(uri, offset, limit, more):
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit
    pager = {
        '@id': '{}&offset={}&limit={}'.format(uri, offset, limit),
        'firstPage': '{}&offset=0&limit={}'.format(uri, limit),
        'paginatedProperty': 'edges'
    }
    if offset > 0:
        pager['previousPage'] = '{}&offset={}&limit={}'.format(uri, prev_offset, limit)
    if more:
        pager['nextPage'] = '{}&offset={}&limit={}'.format(uri, next_offset, limit)
    return pager


class AssertionFinder(object):
    def __init__(self, index_filename=None, edge_filename=None):
        self._index_filename = index_filename or get_data_filename('old/db/assertions.index')
        self._edge_filename = edge_filename or get_data_filename('old/assertions/assertions.msgpack')
        self.search_index = None

    def load_index(self):
        """
        Load the assertion index, if it isn't loaded already.
        """
        if self.search_index is None:
            self.search_index = HashTableIndex(self._index_filename)
        self.edge_file = open(self._edge_filename, 'rb')

    def lookup(self, query, limit=1000, offset=0):
        """
        Look up all assertions associated with the given URI or string
        property. Any of these fields can be matched:

            ['rel', 'start', 'end', 'dataset', 'sources', 'uri', 'features']
        """
        self.load_index()
        if query.endswith('/.'):
            # We can't filter for complete matches here, but let's at least
            # deal with the syntax
            query = query[:-2]
        pointers = self.search_index.lookup(query)
        for i, pointer in enumerate(pointers[offset:]):
            if i >= limit:
                return
            val = transform_for_linked_data(read_msgpack_value(self.edge_file, pointer))
            if not isinstance(val, dict):
                raise IOError(
                    "Couldn't find a dictionary in %r at byte offset %d"
                    % (self.edge_file, pointer)
                )
            if 'context' in val:
                del val['context']
            yield val

    def lookup_random(self):
        self.load_index()
        pointer = self.search_index.weighted_random()
        return transform_for_linked_data(read_msgpack_value(self.edge_file, pointer))

    def lookup_grouped_by_feature(self, query, scan_limit=200, group_limit=10):
        """
        Given a query for a concept, return assertions about that concept grouped by
        their features (for example, "A dog wants to ..." could be a group).

        It will scan up to `scan_limit` assertions to find out which features exist,
        then retrieve `group_limit` assertions for each feature if possible.
        """
        groups = defaultdict(list)
        more = set()
        for assertion in self.lookup(query, limit=scan_limit):
            groupkeys = []
            start = uri_prefix(assertion['start'])
            rel = assertion['rel']
            end = uri_prefix(assertion['end'])
            symmetric = rel in SYMMETRIC_RELATIONS
            if symmetric:
                groupkeys.append((('rel', rel), ('node', uri_prefix(query))))
            else:
                if field_match(assertion['start'], query):
                    groupkeys.append((('rel', rel), ('start', start)))
                if field_match(assertion['end'], query):
                    groupkeys.append((('rel', rel), ('end', end)))
            for groupkey in groupkeys:
                print(groupkey)
                if len(groups[groupkey]) < group_limit:
                    groups[groupkey].append(assertion)
                else:
                    more.add(groupkey)

        for groupkey in groups:
            if len(groups[groupkey]) < group_limit:
                num_more = group_limit - len(groups[groupkey])
                for feature in groupkey_to_features(groupkey):
                    # TODO: alternate between features when there are
                    # multiple possibilities?
                    for assertion in self.lookup(feature, limit=num_more):
                        groups[groupkey].append(assertion)

        grouped = []
        for groupkey in groups:
            base_uri = '/query?'
            group_uri = base_uri + groupkey_to_query(groupkey)
            assertions = groups[groupkey]
            group = {
                '@id': group_uri,
                'largest_weight': max(assertion['weight'] for assertion in assertions),
                'edges': assertions
            }
            if groupkey in more:
                view = make_paginated_view(group_uri, 0, group_limit, more=True)
                group['view'] = view
            grouped.append(group)

        grouped.sort(key=lambda g: -g['largest_weight'])
        for group in grouped:
            del group['largest_weight']
        return grouped

    def query(self, criteria, limit=20, offset=0, scan_limit=200):
        """
        Given a dictionary of criteria, return up to `limit` assertions that
        match all of the criteria.

        For example, a query for the criteria

            {'rel': '/r/TranslationOf', 'end': '/c/en/example'}

        will return assertions such as

            {
                'start': '/c/tr/örnek',
                'rel': '/r/TranslationOf',
                'end': '/c/en/example/n',
                ...
            }
        """
        self.load_index()
        if not criteria:
            return []

        criterion_pairs = sorted(list(criteria.items()))
        features = []
        if 'start' in criteria and 'end' in criteria:
            features = ['{} - {}'.format(uri_prefix(criteria['start']),
                                         uri_prefix(criteria['end']))]
        elif 'start' in criteria and 'rel' in criteria:
            features = ['{} {} -'.format(uri_prefix(criteria['start']),
                                         uri_prefix(criteria['rel']))]
        elif 'rel' in criteria and 'end' in criteria:
            features = ['- {} {}'.format(uri_prefix(criteria['rel']),
                                         uri_prefix(criteria['end']))]
        elif 'rel' in criteria and 'node' in criteria:
            node = uri_prefix(criteria['node'])
            rel = uri_prefix(criteria['rel'])
            features = [
                '{} {} -'.format(node, rel),
                '- {} {}'.format(rel, node)
            ]

        if features:
            queries = [self.lookup(feature, limit=scan_limit)
                       for feature in features]
        else:
            queries = [
                self.lookup(val, limit=scan_limit)
                for (key, val) in criterion_pairs
                if key in INDEXED_KEYS
            ]

        queryzip = zip(*queries)

        matches = []
        done = False
        for result_set in queryzip:
            for candidate in result_set:
                if candidate is None:
                    done = True
                else:
                    okay = True
                    for key, val in criterion_pairs:
                        if key == 'node':
                            matchable = [candidate['start'], candidate['end']]
                        else:
                            matchable = [candidate[key]]
                        if not field_match(matchable, val):
                            okay = False
                            break
                    if okay:
                        matches.append(candidate)
                        if len(matches) >= offset + limit:
                            return matches[offset:]
            if done:
                break
        return matches[offset:]

FINDER = AssertionFinder()
lookup = FINDER.lookup
query = FINDER.query

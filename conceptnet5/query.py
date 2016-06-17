"""
Tools for looking up data in ConceptNet, such as the edges (assertions)
surrounding a particular node (concept). Provides the AssertionFinder,
"""

from conceptnet5.uri import uri_prefix
from conceptnet5.edges import transform_for_linked_data
from conceptnet5.util import get_data_filename
from conceptnet5.formats.msgpack_stream import read_msgpack_value
from conceptnet5.hashtable.index import HashTableIndex


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


class AssertionFinder(object):
    def __init__(self, index_filename=None, edge_filename=None):
        self._index_filename = index_filename or get_data_filename('index/assertions.index')
        self._edge_filename = edge_filename or get_data_filename('assertions/assertions.msgpack')
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
            queries = [self.lookup(feature, limit=limit)
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

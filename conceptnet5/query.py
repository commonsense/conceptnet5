from conceptnet5.util import get_data_filename
from conceptnet5.formats.msgpack_stream import read_msgpack_value
from conceptnet5.hashtable.index import HashTableIndex
from collections import defaultdict


VALID_KEYS = {
    'rel', 'start', 'end', 'dataset', 'license', 'sources',
    'surfaceText', 'uri'
}
INDEXED_KEYS = {
    'rel', 'start', 'end', 'dataset', 'sources',
    'surfaceText', 'uri'
}


def field_match(value, query):
    """
    Determines whether a given field of an edge (or, in particular, an
    assertion) matches the given query.

    If the query is a URI, it will match prefixes of longer URIs, unless
    `/.` is added to the end of the query.

    For example, `/c/en/dog` will match assertions about `/c/en/dog/n/animal`,
    but `/c/en/dog/.` will only match assertions about `/c/en/dog`.
    """
    query = query.rstrip('/')
    if isinstance(value, list):
        return any(field_match(subval, query) for subval in value)
    elif query.endswith('/.'):
        return value == query[:-2]
    else:
        return (value[:len(query)] == query and
                (len(value) == len(query) or value[len(query)] == '/'))


class AssertionFinder(object):
    def __init__(self, index_filename=None, edge_filename=None):
        self._index_filename = index_filename or get_data_filename('db/assertions.index')
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
            val = read_msgpack_value(self.edge_file, pointer)
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
        return read_msgpack_value(self.edge_file, pointer)

    def lookup_grouped_by_feature(self, query, scan_limit=200, group_limit=10, offset=0):
        """
        Given a query for a concept, return assertions about that concept grouped by
        their features (for example, "A dog wants to ..." could be a group).

        It will scan up to `scan_limit` assertions to find out which features exist,
        then retrieve `group_limit` assertions for each feature if possible.
        """
        groups = defaultdict(list)
        more = set()
        for assertion in self.lookup(query, limit=scan_limit, offset=offset):
            groupkeys = []
            if field_match(assertion['start'], query):
                groupkeys.append('%s %s -' % (assertion['start'], assertion['rel']))
            if field_match(assertion['end'], query):
                groupkeys.append('- %s %s' % (assertion['rel'], assertion['end']))
            for groupkey in groupkeys:
                if len(groups[groupkey]) < group_limit:
                    groups[groupkey].append(assertion)
                else:
                    more.add(groupkey)

        for groupkey in groups:
            if len(groups[groupkey]) < group_limit:
                num_more = group_limit - len(groups[groupkey])
                for assertion in self.lookup(groupkey, limit=num_more):
                    groups[groupkey].append(assertion)

        grouped = []
        for groupkey in groups:
            assertions = groups[groupkey]
            grouped.append({
                'feature': groupkey,
                'more': groupkey in more,
                'largest_weight': max(assertion['weight'] for assertion in assertions),
                'assertions': assertions
            })

        grouped.sort(key=lambda g: -g['largest_weight'])
        return grouped

    def query(self, criteria, search_key=None, limit=20, offset=0,
              scan_limit=1000):
        """
        Given a dictionary of criteria, return up to `limit` assertions that
        match all of the criteria.

        For example, a query for the criteria

            {'rel': '/r/TranslationOf', 'end': '/c/en/example'}

        will return assertions such as

            {
                'start': '/c/tr/örnek/',
                'rel': '/r/TranslationOf/',
                'end': '/c/en/example/n/something_representative_of_a_group',
                ...
            }
        """
        self.load_index()
        if not criteria:
            return []

        queries = []
        criterion_pairs = sorted(list(criteria.items()))
        if search_key is not None:
            if search_key not in VALID_KEYS:
                raise KeyError("Unknown criterion: %s" % search_key)
            search_value = criteria[search_key].rstrip('/')
            queries = [self.lookup(search_value, limit=scan_limit)]
        else:
            queries = [
                self.lookup(val, limit=scan_limit)
                for (key, val) in criterion_pairs
                if key in INDEXED_KEYS
            ]

        queryzip = zip(*queries)

        matches = []
        for result_set in queryzip:
            for candidate in result_set:
                if candidate is not None:
                    okay = True
                    for key, val in criterion_pairs:
                        if not field_match(candidate[key], val):
                            okay = False
                            break
                    if okay:
                        matches.append(candidate)
                        if len(matches) >= offset + limit:
                            return matches[offset:]
        return matches[offset:]

FINDER = AssertionFinder()
lookup = FINDER.lookup
query = FINDER.query

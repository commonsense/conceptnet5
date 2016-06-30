"""
Tools for looking up data in ConceptNet, such as the edges (assertions)
surrounding a particular node (concept). Provides the AssertionFinder, a
lazily-loaded object for looking up assertions in a hashtable index
(see the conceptnet5.hashtable package).
"""

from conceptnet5.uri import uri_prefix, is_concept, split_uri
from conceptnet5.edges import transform_for_linked_data
from conceptnet5.util import get_data_filename
from conceptnet5.formats.msgpack_stream import read_msgpack_value
from conceptnet5.hashtable.index import HashTableIndex


VALID_KEYS = {
    'rel', 'start', 'end', 'node', 'dataset', 'license', 'source', 'sources',
    'surfaceText', 'uri'
}
INDEXED_KEYS = {
    'rel', 'start', 'end', 'node', 'dataset', 'source', 'sources',
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
    """
    A lazily-loaded object for looking up assertions in an index.
    """
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
        property. An assertion will match if the query matches any of these
        fields:

            ['rel', 'start', 'end', 'dataset', 'sources', 'uri', 'features']
        """
        self.load_index()
        if query.endswith('/.'):
            # Ending a URI with '/.' has been used as a way to ask for only
            # complete matches. It would actually be difficult to filter for
            # complete matches here, but we can at least cope with the syntax
            # and return the matches we would otherwise return.
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
        """
        Get a random assertion from the index.
        """
        self.load_index()
        pointer = self.search_index.weighted_random()
        return transform_for_linked_data(read_msgpack_value(self.edge_file, pointer))

    def query(self, criteria, limit=20, offset=0, scan_limit=200):
        """
        Given a dictionary of criteria, return up to `limit` assertions that
        match all of the criteria.

        For example, a query for the criteria

            {'rel': '/r/Synonym', 'end': '/c/en/example'}

        will return assertions such as

            {
                'start': '/c/tr/örnek',
                'rel': '/r/Synonym',
                'end': '/c/en/example/n',
                ...
            }
        """
        self.load_index()
        if not criteria:
            return []

        # Certain pairs of criteria, such as 'start' and 'rel', can be
        # looked up quickly by turning them into features that we have
        # already indexed. Find out if we can transform the given criteria.
        criterion_pairs = sorted(list(criteria.items()))

        searchable_criteria = dict(criteria)
        for nodetype in ('start', 'end'):
            if nodetype in searchable_criteria:
                node = searchable_criteria[nodetype]
                if is_concept(node) and len(split_uri(node)) < 3:
                    del searchable_criteria[nodetype]

        searchable_criterion_pairs = sorted(list(searchable_criteria.items()))

        features = []
        if 'start' in searchable_criteria and 'end' in searchable_criteria:
            features = ['{} - {}'.format(uri_prefix(searchable_criteria['start']),
                                         uri_prefix(searchable_criteria['end']))]
        elif 'start' in searchable_criteria and 'rel' in searchable_criteria:
            features = ['{} {} -'.format(uri_prefix(searchable_criteria['start']),
                                         uri_prefix(searchable_criteria['rel']))]
        elif 'rel' in searchable_criteria and 'end' in searchable_criteria:
            features = ['- {} {}'.format(uri_prefix(searchable_criteria['rel']),
                                         uri_prefix(searchable_criteria['end']))]
        elif 'rel' in searchable_criteria and 'node' in searchable_criteria:
            node = uri_prefix(searchable_criteria['node'])
            rel = uri_prefix(searchable_criteria['rel'])
            features = [
                '{} {} -'.format(node, rel),
                '- {} {}'.format(rel, node)
            ]

        # If we could turn the query into a query on features, use that.
        # Otherwise, we'll need to look up the query criteria separately,
        # intersperse their results, and filter for the ones that match
        # all the criteria.
        if features:
            queries = [self.lookup(feature, limit=limit)
                       for feature in features]
        else:
            queries = [
                self.lookup(val, limit=scan_limit)
                for (key, val) in searchable_criterion_pairs
                if key in INDEXED_KEYS
            ]

        # If we made multiple queries, group their results into tuples:
        # for example, the first match to each of the queries, then the second
        # match to each of the queries, and so on. We'll iterate through this
        # zipped list of assertions that match *any* of the criteria, looking
        # for assertions that match *all* of the criteria.
        #
        # Querying by different criteria gives us a better chance of finding
        # intersections, as one of the criteria is probably sufficiently
        # specific that any intersections that exist will show up fairly soon.
        # We may end up missing results in cases where each criterion matches
        # a lot of assertions, but few assertions match all the criteria.
        #
        # This list can end as soon as any of the lists it's built from ends.
        # If one of the lists ends before the others, that means the list was
        # complete, and any match to our criteria must have already shown up
        # in it.
        queryzip = zip(*queries)

        matches = []
        seen = set()
        for result_set in queryzip:
            for candidate in result_set:
                # Find out if the candidate matched all of our criteria, by
                # setting okay=False when one fails to match.
                okay = True
                if candidate['@id'] in seen:
                    continue
                seen.add(candidate['@id'])
                for key, val in criterion_pairs:
                    # If the criterion is 'node', either the start or end is
                    # allowed to match. Otherwise, the field with the same
                    # name as the criterion needs to match.
                    if key == 'node':
                        matchable = [candidate['start'], candidate['end']]
                    elif key == 'source':
                        matchable = [candidate['sources']]
                    else:
                        matchable = [candidate[key]]
                    if not field_match(matchable, val):
                        okay = False
                        break
                if okay:
                    matches.append(candidate)
                    if len(matches) >= offset + limit:
                        return matches[offset:]

        return matches[offset:]


# Make a global default AssertionFinder and some convenient functions for
# using it
FINDER = AssertionFinder()
lookup = FINDER.lookup
query = FINDER.query

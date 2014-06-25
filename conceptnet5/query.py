from conceptnet5.util import get_data_filename
from conceptnet5.formats.sql import EdgeIndexReader


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
    if isinstance(value, list):
        return any(field_match(subval, query) for subval in value)
    elif query.endswith('/.'):
        return value == query[:-2]
    else:
        return value[:len(query)] == query


class AssertionFinder(object):
    def __init__(self, db_filename=None, edge_dir=None):
        self.search_index = None
        self._db_filename = db_filename or get_data_filename('db/assertions.db')
        self._edge_dir = edge_dir or get_data_filename('assertions')

    def load_index(self):
        """
        Load the SQLite index, if it isn't loaded already.
        """
        if self.search_index is None:
            self.search_index = EdgeIndexReader(
                self._db_filename, self._edge_dir
            )

    def lookup(self, query, limit=20, offset=0):
        """
        Look up all assertions associated with the given URI or string
        property.

        If the query is a URI, it will match prefixes of longer URIs, unless
        `/.` is added to the end of the query.

        For example, `/c/en/dog` will match assertions about
        `/c/en/dog/n/animal`, but `/c/en/dog/.` will only match assertions
        about `/c/en/dog`.
        """
        self.load_index()
        if query.endswith('/.'):
            complete = True
            query = query[:-2]
        else:
            complete = False
        return self.search_index.lookup(query, complete, limit=limit, offset=offset)

    def query(self, criteria, search_key=None, limit=20, offset=0):
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

        if search_key is not None:
            if search_key not in VALID_KEYS:
                raise KeyError("Unknown criterion: %s" % search_key)
            main_query = criteria[search_key]
        else:
            # Find the criterion with the longest query, which will probably
            # be the most specific match
            criterion_pairs = [(key, val) for (key, val) in criteria.items()
                               if key in INDEXED_KEYS]
            criterion_pairs.sort(lambda pair: -len(pair[1]))
            if len(criterion_pairs) == 0:
                raise ValueError(
                    "None of these criteria are searchable: %s"
                    % criteria.keys()
                )
            main_query = criterion_pairs[0][1]

        matches = []
        for candidate in self.lookup(main_query, limit=None):
            okay = True
            for key, val in criterion_pairs:
                if not field_match(candidate[key], val):
                    okay = False
                    break
            if okay:
                matches.append(candidate)
                if len(matches) >= offset + limit:
                    break
        return matches[offset:]

FINDER = AssertionFinder()
lookup = FINDER.lookup
query = FINDER.query

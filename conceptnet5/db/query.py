import itertools
import json

from conceptnet5.db.config import DB_NAME
from conceptnet5.db.connection import get_db_connection
from conceptnet5.edges import transform_for_linked_data
from ftfy.fixes import remove_control_chars

LIST_QUERIES = {}
FEATURE_QUERIES = {}

if DB_NAME == 'conceptnet-test':
    # Random queries sample 10% of edges. This makes sure we get matches in
    # the test database, where there isn't much data.
    RANDOM_QUERY = """
        SELECT uri, data, weight FROM edges
        TABLESAMPLE SYSTEM(10)
        ORDER BY random() LIMIT %(limit)s
    """
else:
    # In the real database, random queries sample 0.01% of edges.
    RANDOM_QUERY = """
        SELECT uri, data, weight FROM edges
        TABLESAMPLE SYSTEM(0.01)
        ORDER BY random() LIMIT %(limit)s
    """

# A query that's optimized for producing the edges, grouped by feature, that
# you get when you look up a concept in the Web interface.
NODE_TO_FEATURE_QUERY = """
SELECT rf.direction, r.uri, e.data
FROM ranked_features rf, edges e, relations r
WHERE rf.node_id = (SELECT n.id FROM nodes n where n.uri=%(node)s)
AND rf.edge_id = e.id
AND rf.rel_id = r.id
AND rank <= %(limit)s
ORDER BY direction, uri, rank;
"""

# Queries that match arbitrary criteria using a GIN index. The @> operator
# tests whether one JSONB structure includes all the values in another.
GIN_QUERY_1WAY = """
WITH matched_edges AS (
    SELECT edge_id FROM edges_gin
    WHERE data @> %(query)s
    LIMIT 10000
)
SELECT e.uri, e.data, e.weight
FROM matched_edges m, edges e
WHERE m.edge_id = e.id
ORDER BY weight DESC
OFFSET %(offset)s LIMIT %(limit)s;
"""

GIN_QUERY_2WAY = """
WITH matched_edges AS (
    SELECT edge_id FROM edges_gin
    WHERE data @> %(query_forward)s OR data @> %(query_backward)s
    LIMIT 10000
)
SELECT e.uri, e.data, e.weight
FROM matched_edges m, edges e
WHERE m.edge_id = e.id
ORDER BY weight DESC
OFFSET %(offset)s LIMIT %(limit)s;
"""


def jsonify(value):
    """
    Convert a value into a JSON string that can be used for JSONB queries in
    Postgres.

    If a string happens to contain the character U+0000, which cannot be
    represented in a PostgreSQL value, remove the escape sequence representing
    that character, effectively stripping out that character from all strings.
    """
    return json.dumps(value, ensure_ascii=False).replace("\\u0000", "")


def gin_jsonb_value(criteria, node_forward=True):
    """
    Convert the given criteria into a query that matches the `edges_gin`
    table using the JSONB @> operator.

    In the table, we replace the 'start', 'end', 'rel', and 'dataset' URIs
    with lists of their URI prefixes. We query those slots with a
    single-element list, which will be a sub-list of the prefix list if
    it's a match.

    As an example, a query for {'start': '/c/en'} will become the GIN
    query {'start': ['/c/en']}, which will match indexed edges such as
    {
        'start': ['/c/en', '/c/en/dog'],
        'end': ['/c/en', '/c/en/bark'],
        'rel': ['/r/CapableOf'],
        ...
    }

    Bi-directional queries such as {'node': '/c/en/dog'} have to become two
    separate query dictionaries, one where 'node' is 'start' and 'other' is
    'end', and one where 'node' is 'end' and 'other' is 'start'.

    For that case, we take the optional `node_forward` argument that
    determines the mapping, and call this function twice, once where
    `node_forward` is True and once where it is False.
    """
    criteria_map = {
        'start': 'start',
        'end': 'end',
        'rel': 'rel',
        'dataset': 'dataset',
        # edges have a 'sources' element, but the query key we've historically
        # accepted is 'source', so let's just accept both
        'source': 'sources',
        'sources': 'sources',
    }
    if node_forward:
        criteria_map['node'] = 'start'
        criteria_map['other'] = 'end'
    else:
        criteria_map['node'] = 'end'
        criteria_map['other'] = 'start'

    query = {}
    for criterion_in, criterion_out in criteria_map.items():
        if criterion_in in criteria:
            assert isinstance(criteria[criterion_in], str)
            query[criterion_out] = [criteria[criterion_in]]
    return query


class AssertionFinder(object):
    """
    The object that interacts with the database to find ConcetNet assertions
    (edges) matching certain criteria.
    """

    def __init__(self, dbname=None):
        self.connection = None
        self.dbname = dbname

    def lookup(self, uri, limit=100, offset=0):
        """
        A query that returns all the edges that include a certain URI.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        if uri.startswith('/c/') or uri.startswith('http'):
            criteria = {'node': uri}
        elif uri.startswith('/r/'):
            criteria = {'rel': uri}
        elif uri.startswith('/s/'):
            criteria = {'source': uri}
        elif uri.startswith('/d/'):
            criteria = {'dataset': uri}
        elif uri.startswith('/a/'):
            return self.lookup_assertion(uri)
        else:
            raise ValueError("%r isn't a ConceptNet URI that can be looked up")
        return self.query(criteria, limit, offset)

    def lookup_grouped_by_feature(self, uri, limit=20):
        """
        The query used by the browseable interface, which groups its results
        by what 'feature' they describe of the queried node.

        A feature is defined by the relation, the queried node, and the direction
        (incoming or outgoing).
        """
        uri = remove_control_chars(uri)
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)

        def extract_feature(row):
            return tuple(row[:2])

        def feature_data(row):
            direction, _, data = row

            # Hacky way to figure out what the 'other' node is, the one that
            # (in most cases) didn't match the URI. If both start with our
            # given URI, take the longer one, which is either a more specific
            # sense or a different, longer word.
            shorter, longer = sorted([data['start'], data['end']], key=len)
            if shorter.startswith(uri):
                data['other'] = longer
            else:
                data['other'] = shorter
            return data

        cursor = self.connection.cursor()
        cursor.execute(NODE_TO_FEATURE_QUERY, {'node': uri, 'limit': limit})
        results = {}
        for feature, rows in itertools.groupby(cursor.fetchall(), extract_feature):
            results[feature] = [
                transform_for_linked_data(feature_data(row)) for row in rows
            ]
        return results

    def lookup_assertion(self, uri):
        """
        Get a single assertion, given its URI starting with /a/.
        """
        # Sanitize URIs to remove control characters such as \x00. The postgres driver would
        # remove \x00 anyway, but this avoids reporting a server error when that happens.
        uri = remove_control_chars(uri)
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        cursor.execute("SELECT data FROM edges WHERE uri=%(uri)s", {'uri': uri})
        results = [transform_for_linked_data(data) for (data,) in cursor.fetchall()]
        return results

    def random_edges(self, limit=20):
        """
        Get a collection of distinct, randomly-selected edges.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        cursor.execute(RANDOM_QUERY, {'limit': limit})
        results = [
            transform_for_linked_data(data) for uri, data, weight in cursor.fetchall()
        ]
        return results

    def query(self, criteria, limit=20, offset=0):
        """
        The most general way to query based on a set of criteria.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)

        cursor = self.connection.cursor()
        if 'node' in criteria:
            query_forward = gin_jsonb_value(criteria, node_forward=True)
            query_backward = gin_jsonb_value(criteria, node_forward=False)
            cursor.execute(
                GIN_QUERY_2WAY,
                {
                    'query_forward': jsonify(query_forward),
                    'query_backward': jsonify(query_backward),
                    'limit': limit,
                    'offset': offset,
                },
            )
        else:
            query = gin_jsonb_value(criteria)
            cursor.execute(
                GIN_QUERY_1WAY,
                {'query': jsonify(query), 'limit': limit, 'offset': offset},
            )

        results = [
            transform_for_linked_data(data) for uri, data, weight in cursor.fetchall()
        ]
        return results

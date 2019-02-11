from conceptnet5.db.connection import get_db_connection
from conceptnet5.edges import transform_for_linked_data
import json
import itertools
from ftfy.fixes import remove_control_chars

NODE_PREFIX_CRITERIA = {'node', 'other', 'start', 'end'}
LIST_QUERIES = {}
FEATURE_QUERIES = {}

RANDOM_QUERY = "SELECT uri, data FROM edges TABLESAMPLE SYSTEM(0.01) ORDER BY random() LIMIT %(limit)s"
RANDOM_NODES_QUERY = "SELECT * FROM nodes TABLESAMPLE SYSTEM(1) WHERE uri LIKE :prefix ORDER BY random() LIMIT %(limit)s"
DATASET_QUERY = "SELECT uri, data FROM edges TABLESAMPLE SYSTEM(0.01) WHERE data->'dataset' = %(dataset)s ORDER BY weight DESC OFFSET %(offset)s LIMIT %(limit)s"


TOO_BIG_PREFIXES = ['/c/en', '/c/fr', '/c/es', '/c/de', '/c/ja', '/c/zh',
                    '/c/pt', '/c/la', '/c/it', '/c/ru' ,'/c/fi']

NODE_TO_FEATURE_QUERY = """
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri=%(node)s
    LIMIT 10
)
SELECT rf.direction, r.uri, e.data
FROM ranked_features rf, edges e, relations r
WHERE rf.node_id IN (SELECT node_id FROM node_ids)
AND rf.edge_id = e.id
AND rf.rel_id = r.id
AND rank <= %(limit)s
ORDER BY direction, uri, rank;
"""
MAX_GROUP_SIZE = 20


def make_list_query(criteria):
    """
    Given a dictionary of criteria being searched for, construct the SQL
    query for it.

    This may require the union of two queries (one for outgoing edges and one
    for incoming), and it may require saving certain query criteria for last
    because we know they match too many things.

    We don't substitute in the actual values of the criteria here -- that's
    PostgreSQL's job. We just return a properly parameterized query.
    """
    # Look up the given criteria in the cache, and use the cached query if available
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in LIST_QUERIES:
        return LIST_QUERIES[crit_tuple]

    # Start the inner query, finding edges that match the criteria
    parts = ["WITH matched_edges AS ("]
    # If this is a 'node' query, it happens as the union of two parts: the outgoing
    # direction (1) and the incoming direction (-1).
    if 'node' in criteria or 'filter_node' in criteria:
        piece_directions = [1, -1]
    else:
        piece_directions = [1]
    # Construct the parts of the union
    for direction in piece_directions:
        # If this is the incoming part (the second one), put the "UNION ALL" keyword
        # between the parts that we want to union
        if direction == -1:
            parts.append("UNION ALL")

        parts.append("SELECT e.uri, e.weight, e.data")
        # If we need to do some after-the-fact filtering, select the URIs of the
        # things we're filtering on.
        if 'filter_start' in criteria or 'filter_end' in criteria:
            parts.append(", np1.uri as start_uri, np2.uri as end_uri")
        # If the filter is 'filter_node' or 'filter_other', do the bookkeeping
        # for each direction to remember which one was 'node' and which one was
        # 'other'.
        if 'filter_node' in criteria or 'filter_other' in criteria:
            if direction == 1:
                parts.append(", np1.uri as node_uri, np2.uri as other_uri")
            else:
                parts.append(", np2.uri as node_uri, np1.uri as other_uri")

        # Name the tables that we need to join. We select from the nodes table
        # as 'n1' and 'n2' to find the nodes that actually participate in the
        # query, and 'np1' and 'np2' to get node IDs that we match against the
        # 'node_prefixes' table.
        parts.append("""
            FROM relations r, edges e, nodes n1, nodes n2,
                 node_prefixes p1, node_prefixes p2, nodes np1, nodes np2
        """)
        if 'source' in criteria:
            parts.append(", edge_sources es, sources s")

        parts.append("""
            WHERE e.relation_id=r.id
            AND e.start_id=n1.id
            AND e.end_id=n2.id
            AND p1.prefix_id=np1.id
            AND p1.node_id=n1.id
            AND p2.prefix_id=np2.id
            AND p2.node_id=n2.id
        """)

        # Apply the criteria...
        if 'source' in criteria:
            parts.append("AND s.uri=%(source)s AND es.source_id=s.id AND es.edge_id=e.id")
        # But don't apply the criteria that we said to filter later
        if 'node' in criteria and 'filter_node' not in criteria:
            if direction == 1:
                parts.append("AND np1.uri = %(node)s")
            else:
                parts.append("AND np2.uri = %(node)s")
        if 'other' in criteria and 'filter_other' not in criteria:
            if direction == 1:
                parts.append("AND np2.uri = %(other)s")
            else:
                parts.append("AND np1.uri = %(other)s")
        if 'rel' in criteria:
            parts.append("AND r.uri = %(rel)s")
        if 'start' in criteria and 'filter_start' not in criteria:
            parts.append("AND np1.uri = %(start)s")
        if 'end' in criteria and 'filter_end' not in criteria:
            parts.append("AND np2.uri = %(end)s")

    # Put a reasonable limit on how many edges this inner query can match.
    # This keeps a bound on the runtime but it means that you can't see more
    # than 10000 results of a query in total.
    parts.append("LIMIT 10000")
    parts.append(")")

    # That was the inner query. Now extract the information from it, remove
    # duplicate results, and apply the filters we saved for later.
    parts.append("SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges")
    more_clauses = []
    if 'filter_node' in criteria:
        more_clauses.append('node_uri LIKE %(filter_node)s')
    if 'filter_other' in criteria:
        more_clauses.append('other_uri LIKE %(filter_other)s')
    if 'filter_start' in criteria:
        more_clauses.append('start_uri LIKE %(filter_start)s')
    if 'filter_end' in criteria:
        more_clauses.append('end_uri LIKE %(filter_end)s')
    # We only have a WHERE clause if one of these filters applies
    if more_clauses:
        parts.append("WHERE " + " AND ".join(more_clauses))
    # Sort the results by weight and apply the offset and limit
    parts.append("""
        ORDER BY weight DESC, uri
        OFFSET %(offset)s LIMIT %(limit)s
    """)
    # Put the parts together into one query string
    query = '\n'.join(parts)
    # Cache the query string
    LIST_QUERIES[crit_tuple] = query
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
        elif uri.startswith('/a/'):
            return self.lookup_assertion(uri)
        elif uri.startswith('/d/'):
            return self.sample_dataset(uri, limit, offset)
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
            results[feature] = [transform_for_linked_data(feature_data(row)) for row in rows]
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

    def sample_dataset(self, uri, limit=50, offset=0):
        """
        Get a subsample of edges matching a particular dataset.
        """
        uri = remove_control_chars(uri)
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        dataset_json = json.dumps(uri)
        cursor.execute(DATASET_QUERY, {'dataset': dataset_json, 'limit': limit, 'offset': offset})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def random_edges(self, limit=20):
        """
        Get a collection of distinct, randomly-selected edges.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        cursor.execute(RANDOM_QUERY, {'limit': limit})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def query(self, criteria, limit=20, offset=0):
        """
        The most general way to query based on a set of criteria.
        """
        criteria = criteria.copy()
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        for criterion in ['node', 'other', 'start', 'end']:
            if criterion in criteria and criteria[criterion] in TOO_BIG_PREFIXES:
                criteria['filter_' + criterion] = criteria[criterion] + '%'

        query_string = make_list_query(criteria)
        params = {
            key: remove_control_chars(value)
            for (key, value) in criteria.items()
        }
        params['limit'] = limit
        params['offset'] = offset

        cursor = self.connection.cursor()
        cursor.execute(query_string, params)
        results = [
            transform_for_linked_data(data) for uri, data in cursor.fetchall()
        ]
        return results

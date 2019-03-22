from conceptnet5.db.connection import get_db_connection
from conceptnet5.edges import transform_for_linked_data
import json
import itertools
from ftfy.fixes import remove_control_chars

NODE_PREFIX_CRITERIA = {'node', 'other', 'start', 'end'}
LIST_QUERIES = {}
FEATURE_QUERIES = {}

RANDOM_QUERY = """
    SELECT uri, data, weight FROM edges
    TABLESAMPLE SYSTEM(0.01)
    ORDER BY random() LIMIT %(limit)s
"""
DATASET_QUERY = """
    SELECT uri, data, weight FROM edges
    TABLESAMPLE SYSTEM(0.01)
    WHERE data->>'dataset' = %(dataset)s
    ORDER BY weight DESC
    OFFSET %(offset)s LIMIT %(limit)s
"""

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

    We don't substitute in the actual values of the criteria here -- that's
    PostgreSQL's job. We just return a properly parameterized query.
    """
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in LIST_QUERIES:
        return LIST_QUERIES[crit_tuple]

    if 'node' in criteria and 'other' in criteria:
        parts = _query_parts_node_other(criteria)
    elif 'start' in criteria and 'end' in criteria:
        parts = _query_parts_start_end(criteria)
    elif 'start' in criteria or 'end' in criteria or 'node' in criteria:
        parts = _query_parts_slot(criteria)
    elif 'source' in criteria:
        parts = _query_parts_source(criteria)
    elif 'rel' in criteria:
        parts = _query_parts_rel(criteria)
    else:
        raise ValueError("Can't construct a query for these criteria: %r" % criteria)

    parts.append("""
        ORDER BY weight DESC, uri
        OFFSET %(offset)s LIMIT %(limit)s
    """)
    # Put the parts together into one query string
    query = '\n'.join(parts)
    # Cache the query string
    LIST_QUERIES[crit_tuple] = query
    return query


def _query_parts_node_other(criteria):
    parts = [
        """
        SELECT DISTINCT e.uri as uri, e.data as data, twl.weight as weight
        FROM edges e, nodes n1, nodes n2, two_way_lookup twl
        """
    ]
    if 'source' in criteria:
        parts.append(", sources s, edge_sources es")
    parts.append(
        """
        WHERE e.id = twl.edge_id
        AND twl.node_prefix_id = n1.id AND n1.uri = %(node)s
        AND twl.other_prefix_id = n2.id AND n2.uri = %(other)s
        """
    )
    if 'source' in criteria:
        parts.append("AND es.edge_id = e.id AND es.source_id = s.id")
        parts.append("AND s.uri = %(source)s")
    if 'rel' in criteria:
        parts.append("AND data ->> 'rel' = %(rel)s")
    return parts


def _query_parts_start_end(criteria):
    parts = [
        "SELECT DISTINCT e.uri as uri, e.data as data, twl.weight as weight",
        "FROM edges e, nodes n1, nodes n2, two_way_lookup twl"
    ]
    if 'source' in criteria:
        parts.append(", sources s, edge_sources es")
    parts.append(
        """
        WHERE e.id = twl.edge_id
        AND twl.node_prefix_id = n1.id AND n1.uri = %(start)s
        AND twl.other_prefix_id = n2.id AND n2.uri = %(end)s
        AND direction = 1
        """
    )
    if 'source' in criteria:
        parts.append("AND es.edge_id = e.id AND es.source_id = s.id")
        parts.append("AND s.uri = %(source)s")
    if 'rel' in criteria:
        parts.append("AND data ->> 'rel' = %(rel)s")
    return parts


def _query_parts_source(criteria):
    if (set(criteria) & {'node', 'other', 'start', 'end'}):
        raise ValueError(
            "The 'source' should not be the primary query when we're also "
            "querying by node."
        )
    parts = [
        "SELECT DISTINCT e.uri as uri, e.data as data, e.weight as weight",
        "FROM edges e, edge_sources es, sources s",
        "WHERE es.edge_id = e.id AND es.source_id = s.id",
        "AND s.uri = %(source)s"
    ]
    if 'rel' in criteria:
        parts.append("AND e.data ->> 'rel' = %(rel)s")
    return parts


def _query_parts_slot(criteria):
    parts = [
        "SELECT DISTINCT e.uri as uri, e.data as data, sl.weight as weight",
        "FROM edges e, slot_lookup sl, nodes n"
    ]
    if 'source' in criteria:
        parts.append(", edge_sources es, sources s")
    parts.append("WHERE sl.edge_id = e.id")

    n_criteria = len(set(criteria) & {'start', 'end', 'node'})
    if n_criteria != 1:
        raise ValueError(
            "This function should be used to query by exactly one "
            "node slot, not %d." % n_criteria
        )
    if 'start' in criteria:
        parts.append("AND n.uri = %(start)s AND sl.prefix_id = n.id")
        parts.append("AND sl.slot = 'start'")
    elif 'end' in criteria:
        parts.append("AND n.uri = %(end)s AND sl.prefix_id = n.id")
        parts.append("AND sl.slot = 'end'")
    elif 'node' in criteria:
        parts.append("AND n.uri = %(node)s AND sl.prefix_id = n.id")
        # no slot restriction
    else:
        raise RuntimeError("shouldn't get here")

    if 'source' in criteria:
        parts.append("AND es.edge_id = e.id AND es.source_id = s.id")
        parts.append("AND s.uri = %(source)s")
    if 'rel' in criteria:
        parts.append("AND e.data ->> 'rel' = %(rel)s")
    return parts


def _query_parts_rel(_criteria):
    return [
        "SELECT e.uri as uri, e.data as data, e.weight as weight",
        "FROM edges e, relations r",
        "WHERE e.relation_id = r.id and r.uri=%(uri)s"
    ]


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
        results = [transform_for_linked_data(data) for uri, data, weight in cursor.fetchall()]
        return results

    def random_edges(self, limit=20):
        """
        Get a collection of distinct, randomly-selected edges.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        cursor.execute(RANDOM_QUERY, {'limit': limit})
        results = [transform_for_linked_data(data) for uri, data, weight in cursor.fetchall()]
        return results

    def query(self, criteria, limit=20, offset=0):
        """
        The most general way to query based on a set of criteria.
        """
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)

        # If the only criterion is 'dataset', use sampling instead
        if list(criteria) == ['dataset']:
            return self.sample_dataset(criteria['dataset'])

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
            transform_for_linked_data(data) for uri, data, weight in cursor.fetchall()
        ]
        return results

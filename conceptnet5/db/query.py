from .connection import get_db_connection
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


TOO_BIG_PREFIXES = ['/c/en', '/c/fr', '/c/es', '/c/de', '/c/ja', '/c/zh', '/c/pt', '/c/la', '/c/it', '/c/ru' ,'/c/fi']

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
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in LIST_QUERIES:
        return LIST_QUERIES[crit_tuple]
    parts = ["WITH matched_edges AS ("]
    if 'node' in criteria:
        piece_directions = [1, -1]
    else:
        piece_directions = [1]
    for direction in piece_directions:
        if direction == -1:
            parts.append("UNION ALL")
        parts.append("""
            SELECT e.uri, e.weight, e.data
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
        if 'source' in criteria:
            parts.append("AND s.uri=%(source)s AND es.source_id=s.id AND es.edge_id=e.id")
        if 'node' in criteria:
            if direction == 1:
                parts.append("AND np1.uri = %(node)s")
            else:
                parts.append("AND np2.uri = %(node)s")
        if 'other' in criteria:
            if direction == 1:
                parts.append("AND np2.uri = %(other)s")
            else:
                parts.append("AND np1.uri = %(other)s")
        if 'rel' in criteria:
            parts.append("AND r.uri = %(rel)s")
        if 'start' in criteria:
            parts.append("AND np1.uri = %(start)s")
        if 'end' in criteria:
            parts.append("AND np2.uri = %(end)s")
    parts.append("LIMIT 10000")
    parts.append(")")
    parts.append("""
        SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges
        ORDER BY weight DESC, uri
        OFFSET %(offset)s LIMIT %(limit)s
    """)
    query = '\n'.join(parts)
    LIST_QUERIES[crit_tuple] = query
    return query


class AssertionFinder(object):
    def __init__(self, dbname=None):
        self.connection = None
        self.dbname = dbname

    def lookup(self, uri, limit=100, offset=0):
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
        uri = remove_control_chars(uri)
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        dataset_json = json.dumps(uri)
        cursor.execute(DATASET_QUERY, {'dataset': dataset_json, 'limit': limit, 'offset': offset})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def random_edges(self, limit=20):
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        cursor = self.connection.cursor()
        cursor.execute(RANDOM_QUERY, {'limit': limit})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def query(self, criteria, limit=20, offset=0):
        filter_later = {}
        if self.connection is None:
            self.connection = get_db_connection(self.dbname)
        params = {
            key: remove_control_chars(value)
            for (key, value) in criteria.items()
        }
        params['limit'] = limit
        params['offset'] = offset
        for criterion in ['node', 'other', 'start', 'end']:
            if criterion in criteria and criteria[criterion] in TOO_BIG_PREFIXES:
                filter_later[criterion] = criteria[criterion]
                del criteria[criterion]
                params['limit'] = limit * 10

        query_string = make_list_query(criteria)
        cursor = self.connection.cursor()
        cursor.execute(query_string, params)
        results = [
            transform_for_linked_data(data) for uri, data in cursor.fetchall()
            if match_filter_later(data, filter_later)
        ][:limit]
        return results


def match_filter_later(data, filter_later):
    # TODO: this is spaghetti designed to make the API go back up. Clean up.
    if 'start' in filter_later:
        prefix = filter_later['start'] + '/'
        if not data['start'].startswith(prefix):
            return False

    if 'end' in filter_later:
        prefix = filter_later['end'] + '/'
        if not data['end'].startswith(prefix):
            print(data['end'], prefix)

    # TODO: node and other
    return True


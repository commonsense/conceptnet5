from .connection import get_db_connection
from conceptnet5.relations import ALL_RELATIONS, SYMMETRIC_RELATIONS
from conceptnet5.edges import transform_for_linked_data
from collections import defaultdict
import json


NODE_PREFIX_CRITERIA = {'node', 'other', 'start', 'end'}
LIST_QUERIES = {}
FEATURE_QUERIES = {}

RANDOM_QUERY = "SELECT uri, data FROM edges TABLESAMPLE SYSTEM(0.01) ORDER BY random() LIMIT :limit"
RANDOM_NODES_QUERY = "SELECT * FROM nodes TABLESAMPLE SYSTEM(1) WHERE uri LIKE :prefix ORDER BY random() LIMIT :limit"
DATASET_QUERY = "SELECT uri, data FROM edges WHERE data->'dataset' = :dataset ORDER BY weight DESC OFFSET :offset LIMIT :limit"


NODE_TO_FEATURE_QUERY = """
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri='/c/en/example'
    LIMIT 200
),
matched_edges AS (
    SELECT e.uri, e.weight, e.data, ef.direction, ef.rel_id,
        row_number() OVER (PARTITION BY (ef.rel_id, ef.direction) ORDER BY e.weight DESC, e.id) AS rank
    FROM edges e, edge_features ef
    WHERE ef.node_id in (SELECT node_id FROM node_ids)
    AND ef.edge_id=e.id
)
SELECT direction, rel_id, data FROM matched_edges
WHERE rank <= 21
ORDER BY direction, rel_id, rank;
"""

NODE_TO_FEATURE_QUERY = """
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri='/c/en/example'
    LIMIT 200
)
SELECT e.uri, e.weight, e.data, ef.direction, ef.rel_id
FROM edges e, edge_features ef
WHERE ef.node_id in (SELECT node_id FROM node_ids)
AND ef.rel_id=37
AND ef.edge_id=e.id
ORDER BY e.weight DESC
LIMIT 20;
"""



def make_feature_query(criteria):
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in FEATURE_QUERIES:
        return FEATURE_QUERIES[crit_tuple]
    ...


def make_list_query(criteria):
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in LIST_QUERIES:
        return LIST_QUERIES[crit_tuple]
    parts = ["WITH"]
    for criterion in set(criteria) & NODE_PREFIX_CRITERIA:
        parts.append(
            """
            {c}_ids AS (
                SELECT p.node_id FROM nodes n, node_prefixes p
                WHERE p.prefix_id=n.id AND n.uri=:{c}
                LIMIT 200
            ),
            """.format(c=criterion)
        )
    piece_directions = [1]
    if 'node' in criteria:
        piece_directions = [1, -1]
    parts.append("matched_edges AS (")
    for direction in piece_directions:
        if direction == -1:
            parts.append("UNION ALL")
        parts.append("""
            SELECT e.uri, e.weight, e.data
            FROM relations r, nodes n1, nodes n2, edges e
        """)
        if 'source' in criteria:
            parts.append(", edge_sources es, sources s")
        parts.append("""
            WHERE e.relation_id=r.id
            AND e.start_id=n1.id
            AND e.end_id=n2.id
        """)
        if 'source' in criteria:
            parts.append("AND s.uri=:source AND es.source_id=s.id AND es.edge_id=e.id")
        if 'node' in criteria:
            if direction == 1:
                parts.append("AND n1.id IN (SELECT node_id FROM node_ids)")
            else:
                parts.append("AND n2.id IN (SELECT node_id FROM node_ids)")
        if 'other' in criteria:
            if direction == 1:
                parts.append("AND n2.id IN (SELECT node_id FROM other_ids)")
            else:
                parts.append("AND n1.id IN (SELECT node_id FROM other_ids)")
        if 'rel' in criteria:
            parts.append("AND r.uri = :rel")
        if 'start' in criteria:
            parts.append("AND n1.id IN (SELECT node_id FROM start_ids)")
        if 'end' in criteria:
            parts.append("AND n2.id IN (SELECT node_id FROM end_ids)")
    parts.append("LIMIT 10000")
    parts.append(")")
    parts.append("""
        SELECT uri, data FROM matched_edges
        ORDER BY weight DESC, uri
        OFFSET :offset LIMIT :limit
    """)
    query = '\n'.join(parts)
    LIST_QUERIES[crit_tuple] = query
    return query


class AssertionFinder(object):
    def __init__(self, dbname=None):
        self.connection = get_db_connection(dbname)

    def lookup(self, uri, limit=100, offset=0):
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
            raise ValueError
        return self.query(criteria, limit, offset)

    def lookup_grouped_by_feature(self, uri, feature_limit=20):
        results = defaultdict(list)
        for rel in ALL_RELATIONS:
            print(rel)
            entries = self.query({'start': uri, 'rel': rel}, limit=feature_limit + 1)
            for entry in entries:
                entry['other'] = entry['end']
            direction = 1 * (rel not in SYMMETRIC_RELATIONS)
            if entries:
                results[direction, rel].extend(entries)

            entries = self.query({'end': uri, 'rel': rel}, limit=feature_limit + 1)
            for entry in entries:
                entry['other'] = entry['start']
            direction = -1 * (rel not in SYMMETRIC_RELATIONS)
            if entries:
                combined = (direction, rel) in results
                results[direction, rel].extend(entries)
                if combined:
                    results[direction, rel].sort(
                        key=lambda r: r['weight'], reverse=True,
                    )

        return dict(results)

    def lookup_assertion(self, uri):
        cursor = self.connection.cursor()
        cursor.execute("SELECT data FROM edges WHERE uri=:uri", {'uri': uri})
        results = [transform_for_linked_data(data) for (data,) in cursor.fetchall()]
        return results

    def sample_dataset(self, uri, limit=50, offset=0):
        cursor = self.connection.cursor()
        dataset_json = json.dumps(uri)
        cursor.execute(DATASET_QUERY, {'dataset': dataset_json, 'limit': limit, 'offset': offset})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def random_edges(self, limit=20):
        cursor = self.connection.cursor()
        cursor.execute(RANDOM_QUERY, {'limit': limit})
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

    def query(self, criteria, limit=20, offset=0):
        params = dict(criteria)
        params['limit'] = limit
        params['offset'] = offset
        query_string = make_list_query(criteria)
        cursor = self.connection.cursor()
        cursor.execute(query_string, params)
        results = [transform_for_linked_data(data) for uri, data in cursor.fetchall()]
        return results

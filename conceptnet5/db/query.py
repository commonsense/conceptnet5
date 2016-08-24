from .connection import get_db_connection
import json

# This query takes in two parameters: a node URI and a number of edges per
# feature.
#
# It finds edges whose start or end is the given node, or a sub-sense of that
# node (having the given node URI as a prefix). It groups the edges by what
# feature they express about the node (such as "example UsedFor ..."), and
# returns only the N top-weighted edges for each feature.

FEATURE_QUERY = """
-- This WITH clause is a Common Table Expression, which lets us describe
-- and name the sub-queries we need to run, so that they can be used in the
-- queries further down, possibly multiple times.
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri=:node
    LIMIT 100
),
-- Another clause in the CTE contains the meat of the query, selecting all the
-- edges with one of the node IDs we just got as its start or end. The idea of
-- "start or end" is expressed with a UNION of two similar queries.
matched_edges AS (
    -- This 'location' integer distinguishes whether the start or end matched
    -- the input node.
    SELECT 1 AS location, n0.id AS rel_id,
           e.uri AS uri, e.data AS data, e.weight AS weight,
           -- Attach a rank to each edge, indicating the rank order of its
           -- weight within a relation. Break ties by ID. We'll use this to
           -- prune the results.
           row_number() OVER (PARTITION BY n0.uri ORDER BY e.weight desc, e.id) AS rank
    FROM nodes n0, nodes n1, nodes n2, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND n1.id IN (SELECT node_id FROM node_ids)
    UNION

    -- Here's that same query again, except with n2.id instead of n1.id.
    SELECT 2 AS location, n0.id AS rel_id,
           e.uri AS uri, e.data AS data, e.weight AS weight,
           row_number() OVER (PARTITION BY n0.uri ORDER BY e.weight desc, e.id) AS rank
    FROM nodes n0, nodes n1, nodes n2, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND n2.id IN (SELECT node_id FROM node_ids)
)
-- That's the end of the WITH clause. Finally, we SELECT the results that
-- rank highly enough within their relation.
SELECT uri, data FROM matched_edges
WHERE rank <= :limit
ORDER BY location, rel_id, rank
"""

PREFIX_CRITERIA = {'node', 'other', 'start', 'end', 'source'}
LIST_QUERIES = {}

RANDOM_QUERY = "SELECT uri, data FROM edges TABLESAMPLE SYSTEM(0.01) ORDER BY random() LIMIT :limit"
RANDOM_NODES_QUERY = "SELECT * FROM nodes TABLESAMPLE SYSTEM(0.1) WHERE uri LIKE '/c/%' ORDER BY random() LIMIT :limit"


def make_list_query(criteria):
    crit_tuple = tuple(sorted(criteria))
    if crit_tuple in LIST_QUERIES:
        return LIST_QUERIES[crit_tuple]
    parts = ["WITH"]
    for criterion in set(criteria) & PREFIX_CRITERIA:
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
            FROM nodes n0, nodes n1, nodes n2, edges e
        """)
        if 'source' in criteria:
            parts.append(", edge_sources s")
        parts.append("""
            WHERE e.relation_id=n0.id
            AND e.start_id=n1.id
            AND e.end_id=n2.id
        """)
        if 'source' in criteria:
            parts.append("AND s.edge_id=e.id")
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
            parts.append("AND n0.uri = :rel")
        if 'start' in criteria:
            parts.append("AND n1.id IN (SELECT node_id FROM start_ids)")
        if 'end' in criteria:
            parts.append("AND n2.id IN (SELECT node_id FROM end_ids)")
        if 'source' in criteria:
            parts.append("AND s.source_id IN (SELECT node_id FROM source_ids)")
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
    def __init__(self):
        self.connection = get_db_connection()

    def lookup(self, uri, limit=1000, offset=0):
        if uri.startswith('/c/') or uri.startswith('http'):
            criteria = {'node': uri}
        elif uri.startswith('/r/'):
            criteria = {'rel': uri}
        elif uri.startswith('/s/'):
            criteria = {'source': uri}
        else:
            raise ValueError
        return self.query(criteria, limit, offset)

    def lookup_random(self):
        ...

    def query(self, criteria, limit=20, offset=0):
        params = dict(criteria)
        params['limit'] = limit
        params['offset'] = offset
        query_string = make_list_query(criteria)
        cursor = self.connection.cursor()
        cursor.execute(query_string, params)
        results = [data for uri, data in cursor.fetchall()]
        return results

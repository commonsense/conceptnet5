# This query takes in two parameters: a node URI and a number of edges per
# feature.
#
# It finds edges whose start or end is the given node, or a sub-sense of that
# node (having the given node URI as a prefix). It groups the edges by what
# feature they express about the node (such as "example UsedFor ..."), and
# returns only the N top-weighted edges for each feature.

NODE_PREFIX_QUERY_WITH_FEATURE_LIMIT = """
-- This WITH clause is a Common Table Expression, which lets us describe
-- and name the sub-queries we need to run, so that they can be used in the
-- queries further down, possibly multiple times.
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri=%s
),
-- Another clause in the CTE contains the meat of the query, selecting all the
-- edges with one of the node IDs we just got as its start or end. The idea of
-- "start or end" is expressed with a UNION of two similar queries.
matched_edges AS (
    -- This 'location' integer distinguishes whether the start or end matched
    -- the input node.
    SELECT 1 AS location,
           n0.uri AS rel_uri, n1.uri AS start_uri, n2.uri AS end_uri,
           nd.uri AS dataset_uri, nlic.uri AS license_uri,
           e.weight, e.source_data, e.surface_text, e.start_text, e.end_text,
           -- Attach a rank to each edge, indicating the rank order of its
           -- weight within a relation. Break ties by ID. We'll use this to
           -- prune the results.
           row_number() OVER (PARTITION BY n0.uri ORDER BY e.weight desc, e.id) AS rank
    FROM nodes n0, nodes n1, nodes n2, nodes nd, nodes nlic, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND e.dataset_id=nd.id
      AND e.license_id=nlic.id
      AND n1.id IN (SELECT node_id FROM node_ids)
    UNION

    -- Here's that same query again, except with n2.id instead of n1.id.
    SELECT 2 AS location,
           n0.uri AS rel_uri, n1.uri AS start_uri, n2.uri AS end_uri,
           nd.uri AS dataset_uri, nlic.uri AS license_uri,
           e.weight, e.source_data, e.surface_text, e.start_text, e.end_text,
           row_number() OVER (PARTITION BY n0.uri ORDER BY e.weight desc, e.id) AS rank
    FROM nodes n0, nodes n1, nodes n2, nodes nd, nodes nlic, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND e.dataset_id=nd.id
      AND e.license_id=nlic.id
      AND n2.id IN (SELECT node_id FROM node_ids)
)
-- That's the end of the WITH clause. Finally, we SELECT the results that
-- rank highly enough within their relation.
SELECT location, rel_uri, start_uri, end_uri, dataset_uri, license_uri, weight,
       source_data, surface_text, start_text, end_text
FROM matched_edges
WHERE rank <= %s
ORDER BY location, rel_uri, rank;
"""

# This query returns a ranked list of edges with a given node, or one of its
# sub-senses, as the start or end.
NODE_PREFIX_QUERY = """
WITH node_ids AS (
    SELECT p.node_id FROM nodes n, node_prefixes p
    WHERE p.prefix_id=n.id AND n.uri=%s
),
matched_edges AS (
    -- This 'location' integer distinguishes whether the start or end matched
    -- the input node.
    SELECT 1 AS location,
           n0.uri AS rel_uri, n1.uri AS start_uri, n2.uri AS end_uri,
           nd.uri AS dataset_uri, nlic.uri AS license_uri,
           e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
    FROM nodes n0, nodes n1, nodes n2, nodes nd, nodes nlic, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND e.dataset_id=nd.id
      AND e.license_id=nlic.id
      AND n1.id IN (SELECT node_id FROM node_ids)
    UNION

    -- Here's that same query again, except with n2.id instead of n1.id.
    SELECT 2 AS location,
           n0.uri AS rel_uri, n1.uri AS start_uri, n2.uri AS end_uri,
           nd.uri AS dataset_uri, nlic.uri AS license_uri,
           e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
    FROM nodes n0, nodes n1, nodes n2, nodes nd, nodes nlic, edges e
    WHERE e.relation_id=n0.id
      AND e.start_id=n1.id
      AND e.end_id=n2.id
      AND e.dataset_id=nd.id
      AND e.license_id=nlic.id
      AND n2.id IN (SELECT node_id FROM node_ids)
)
SELECT location, rel_uri, start_uri, end_uri, dataset_uri, license_uri, weight,
       source_data, surface_text, start_text, end_text
FROM matched_edges
ORDER BY weight DESC
LIMIT %s;
"""

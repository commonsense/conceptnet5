import re
from nose.tools import eq_, assert_raises

from conceptnet5.db.query import make_list_query


EXTRA_WHITESPACE_RE = re.compile(r"\s+")
SYMBOL_WHITESPACE_RE = re.compile(r"\s(?=\W)")


def strip_whitespace(query):
    """
    Convert SQL queries to a canonical form that disregards most whitespace
    differences.
    """
    # Replace whitespace sequences with a single space
    query = EXTRA_WHITESPACE_RE.sub(" ", query)
    # Remove whitespace before non-word symbols
    query = SYMBOL_WHITESPACE_RE.sub("", query)
    # Remove surrounding whitespace
    return query.strip()


def whitespace_eq(string1, string2):
    eq_(strip_whitespace(string1), strip_whitespace(string2))


def test_whitespace():
    # Test the test helper functions, so we know they're testing the right thing.
    eq_(strip_whitespace("\tline 1\n\tline 2\n"), "line 1 line 2")
    eq_(strip_whitespace("   text , with   spaces "), "text, with spaces")
    whitespace_eq("   text , with   spaces ", "text,\nwith\nspaces")
    with assert_raises(AssertionError):
        whitespace_eq("   text , with   spaces ", "text\n,with\nspaces")


# The following tests try various different query shapes and make sure they
# return the expected query strings.
#
# The values of the query criteria don't matter. They're only substituted in
# when the query is actually sent to the database, using the proper substitution
# mechanism that avoids SQL injection.

def test_query_start():
    query = make_list_query({'start': 'x'})
    expected = """
    WITH matched_edges AS (
        SELECT e.uri, e.weight, e.data
        FROM relations r, edges e, nodes n1, nodes n2,
             node_prefixes p1, node_prefixes p2, nodes np1, nodes np2
        WHERE e.relation_id=r.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND p1.prefix_id=np1.id
        AND p1.node_id=n1.id
        AND p2.prefix_id=np2.id
        AND p2.node_id=n2.id
        AND np1.uri = %(start)s
        LIMIT 10000
    )
    SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_source():
    query = make_list_query({'source': 'x'})
    expected = """
    WITH matched_edges AS (
        SELECT e.uri, e.weight, e.data
        FROM relations r, edges e, nodes n1, nodes n2,
             node_prefixes p1, node_prefixes p2, nodes np1, nodes np2,
             edge_sources es, sources s
        WHERE e.relation_id=r.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND p1.prefix_id=np1.id
        AND p1.node_id=n1.id
        AND p2.prefix_id=np2.id
        AND p2.node_id=n2.id
        AND s.uri=%(source)s AND es.source_id=s.id AND es.edge_id=e.id
        LIMIT 10000
    )
    SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_end_source():
    query = make_list_query({'end': 'x', 'source': 'x'})
    expected = """
    WITH matched_edges AS (
        SELECT e.uri, e.weight, e.data
        FROM relations r, edges e, nodes n1, nodes n2,
             node_prefixes p1, node_prefixes p2, nodes np1, nodes np2,
             edge_sources es, sources s
        WHERE e.relation_id=r.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND p1.prefix_id=np1.id
        AND p1.node_id=n1.id
        AND p2.prefix_id=np2.id
        AND p2.node_id=n2.id
        AND s.uri=%(source)s AND es.source_id=s.id AND es.edge_id=e.id
        AND np2.uri = %(end)s
        LIMIT 10000
    )
    SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_node():
    query = make_list_query({'node': 'x'})
    expected = """
    WITH matched_edges AS (
        SELECT e.uri, e.weight, e.data
        FROM relations r, edges e, nodes n1, nodes n2,
             node_prefixes p1, node_prefixes p2, nodes np1, nodes np2
        WHERE e.relation_id=r.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND p1.prefix_id=np1.id
        AND p1.node_id=n1.id
        AND p2.prefix_id=np2.id
        AND p2.node_id=n2.id
        AND np1.uri = %(node)s
    UNION ALL
        SELECT e.uri, e.weight, e.data
        FROM relations r, edges e, nodes n1, nodes n2,
             node_prefixes p1, node_prefixes p2, nodes np1, nodes np2
        WHERE e.relation_id=r.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND p1.prefix_id=np1.id
        AND p1.node_id=n1.id
        AND p2.prefix_id=np2.id
        AND p2.node_id=n2.id
        AND np2.uri = %(node)s
        LIMIT 10000
    )
    SELECT DISTINCT ON (weight, uri) uri, data FROM matched_edges
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)

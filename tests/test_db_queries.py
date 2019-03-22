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
    SELECT DISTINCT e.uri as uri, e.data as data, sl.weight as weight
    FROM edges e, slot_lookup sl, nodes n
    WHERE sl.edge_id = e.id
      AND n.uri = %(start)s AND sl.prefix_id = n.id AND sl.slot = 'start'
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_start_end():
    query = make_list_query({'start': 'x', 'end': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, twl.weight as weight
    FROM edges e, nodes n1, nodes n2, two_way_lookup twl
    WHERE e.id = twl.edge_id
      AND twl.node_prefix_id = n1.id AND n1.uri = %(start)s
      AND twl.other_prefix_id = n2.id AND n2.uri = %(end)s
      AND direction = 1
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_node_other():
    query = make_list_query({'node': 'x', 'other': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, twl.weight as weight
    FROM edges e, nodes n1, nodes n2, two_way_lookup twl
    WHERE e.id = twl.edge_id
      AND twl.node_prefix_id = n1.id AND n1.uri = %(node)s
      AND twl.other_prefix_id = n2.id AND n2.uri = %(other)s
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_source():
    query = make_list_query({'source': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, e.weight as weight
    FROM edges e, edge_sources es, sources s
    WHERE es.edge_id = e.id AND es.source_id = s.id AND s.uri = %(source)s
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_end_source():
    query = make_list_query({'end': 'x', 'source': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, sl.weight as weight
    FROM edges e, slot_lookup sl, nodes n, edge_sources es, sources s
    WHERE sl.edge_id = e.id
      AND n.uri = %(end)s AND sl.prefix_id = n.id AND sl.slot = 'end'
      AND es.edge_id = e.id AND es.source_id = s.id AND s.uri = %(source)s
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_node():
    query = make_list_query({'node': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, sl.weight as weight
    FROM edges e, slot_lookup sl, nodes n
    WHERE sl.edge_id = e.id
      AND n.uri = %(node)s AND sl.prefix_id = n.id
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)


def test_query_node_rel():
    query = make_list_query({'node': 'x', 'rel': 'x'})
    expected = """
    SELECT DISTINCT e.uri as uri, e.data as data, sl.weight as weight
    FROM edges e, slot_lookup sl, nodes n
    WHERE sl.edge_id = e.id
      AND n.uri = %(node)s AND sl.prefix_id = n.id
    AND e.data ->> 'rel' = %(rel)s
    ORDER BY weight DESC, uri
    OFFSET %(offset)s LIMIT %(limit)s
    """
    whitespace_eq(query, expected)

TABLES = [
    "DROP TABLE IF EXISTS edge_sources",
    "DROP TABLE IF EXISTS node_prefixes",
    "DROP TABLE IF EXISTS edges",
    "DROP TABLE IF EXISTS nodes",
    """CREATE TABLE nodes (
        id     integer NOT NULL PRIMARY KEY,
        uri    text NOT NULL
    )""",
    """CREATE TABLE edges (
        id             integer NOT NULL PRIMARY KEY,
        uri            text NOT NULL,
        relation_id    integer NOT NULL REFERENCES nodes (id),
        start_id       integer NOT NULL REFERENCES nodes (id),
        end_id         integer NOT NULL REFERENCES nodes (id),
        weight         real NOT NULL,
        data           jsonb NOT NULL
    )""",
    """CREATE TABLE edge_sources (
        edge_id        integer NOT NULL REFERENCES edges (id),
        source_id      integer NOT NULL REFERENCES nodes (id)
    )
    """,
    """CREATE TABLE node_prefixes (
        node_id        integer NOT NULL REFERENCES nodes (id),
        prefix_id      integer NOT NULL REFERENCES nodes (id)
    )
    """
]

INDICES = [
    "ALTER TABLE nodes ADD CONSTRAINT nodes_unique_uri UNIQUE (uri)",
    "ALTER TABLE edges ADD CONSTRAINT edges_unique_uri UNIQUE (uri)",
    "ALTER TABLE edge_sources ADD CONSTRAINT edge_sources_unique UNIQUE (edge_id, source_id)",
    "ALTER TABLE node_prefixes ADD CONSTRAINT node_prefixes_unique UNIQUE (node_id, prefix_id)",
    "CREATE INDEX edge_relation ON edges (relation_id)",
    "CREATE INDEX edge_start ON edges (start_id)",
    "CREATE INDEX edge_end ON edges (end_id)",
    "CREATE INDEX edge_weight ON edges (weight)",
    "CREATE INDEX edge_search ON edges USING GIN (data jsonb_path_ops)",
    "CREATE INDEX es_edge ON edge_sources (edge_id)",
    "CREATE INDEX es_source ON edge_sources (source_id)",
    "CREATE INDEX np_node ON node_prefixes (node_id)",
    "CREATE INDEX np_prefix ON node_prefixes (prefix_id)"
]

VIEWS = [
    """
    CREATE VIEW edge_prefix_view AS
        SELECT e.id AS edge_id, 'node' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e
        WHERE np.id=p.prefix_id AND p.node_id=e.start_id
    UNION ALL
        SELECT e.id AS edge_id, 'node' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e
        WHERE np.id=p.prefix_id AND p.node_id=e.end_id
    UNION ALL
        SELECT e.id AS edge_id, 'start' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e
        WHERE np.id=p.prefix_id AND p.node_id=e.start_id
    UNION ALL
        SELECT e.id AS edge_id, 'end' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e
        WHERE np.id=p.prefix_id AND p.node_id=e.end_id
    UNION ALL
        SELECT e.id AS edge_id, 'rel' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e
        WHERE np.id=p.prefix_id AND p.node_id=e.end_id
    UNION ALL
        SELECT e.id AS edge_id, 'source' AS key, np.uri AS prefix
        FROM node_prefixes p, nodes np, edges e, edge_sources es
        WHERE np.id=p.prefix_id AND p.node_id=es.source_id AND es.edge_id=e.id
    ;"""
]

def run_commands(connection, commands):
    cursor = connection.cursor()
    for cmd in commands:
        cursor.execute(cmd)
    connection.commit()


def create_tables(connection):
    run_commands(connection, TABLES)


def create_indices(connection):
    run_commands(connection, INDICES)

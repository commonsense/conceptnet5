TABLES = [
    "DROP MATERIALIZED VIEW IF EXISTS ranked_features",
    "DROP TABLE IF EXISTS edge_features",
    "DROP TABLE IF EXISTS edge_sources",
    "DROP TABLE IF EXISTS node_prefixes",
    "DROP TABLE IF EXISTS edges",
    "DROP TABLE IF EXISTS nodes",
    "DROP TABLE IF EXISTS sources",
    "DROP TABLE IF EXISTS relations",
    """CREATE TABLE nodes (
        id     integer NOT NULL PRIMARY KEY,
        uri    text NOT NULL
    )""",
    """CREATE TABLE sources (
        id     integer NOT NULL PRIMARY KEY,
        uri    text NOT NULL
    )""",
    """CREATE TABLE relations (
        id        integer NOT NULL PRIMARY KEY,
        uri       text NOT NULL,
        directed  bool NOT NULL
    )
    """,
    """CREATE TABLE edges (
        id             integer NOT NULL PRIMARY KEY,
        uri            text NOT NULL,
        relation_id    integer NOT NULL REFERENCES relations (id),
        start_id       integer NOT NULL REFERENCES nodes (id),
        end_id         integer NOT NULL REFERENCES nodes (id),
        weight         real NOT NULL,
        data           jsonb NOT NULL
    )""",
    """CREATE TABLE edge_sources (
        edge_id        integer NOT NULL REFERENCES edges (id),
        source_id      integer NOT NULL REFERENCES sources (id)
    )
    """,
    """CREATE TABLE node_prefixes (
        node_id        integer NOT NULL REFERENCES nodes (id),
        prefix_id      integer NOT NULL REFERENCES nodes (id)
    )
    """,
    """CREATE TABLE edge_features (
        rel_id    integer NOT NULL REFERENCES relations (id),
        direction integer NOT NULL,
        node_id   integer NOT NULL REFERENCES nodes (id),
        edge_id   integer NOT NULL REFERENCES edges (id)
    )
    """
]

INDICES = [
    "ALTER TABLE nodes ADD CONSTRAINT nodes_unique_uri UNIQUE (uri)",
    "ALTER TABLE sources ADD CONSTRAINT sources_unique_uri UNIQUE (uri)",
    "ALTER TABLE edges ADD CONSTRAINT edges_unique_uri UNIQUE (uri)",
    "ALTER TABLE relations ADD CONSTRAINT relations_unique_uri UNIQUE (uri)",
    "ALTER TABLE edge_sources ADD CONSTRAINT edge_sources_unique UNIQUE (edge_id, source_id)",
    "ALTER TABLE node_prefixes ADD CONSTRAINT node_prefixes_unique UNIQUE (node_id, prefix_id)",
    "CREATE INDEX edge_relation ON edges (relation_id)",
    "CREATE INDEX edge_start ON edges (start_id)",
    "CREATE INDEX edge_end ON edges (end_id)",
    "CREATE INDEX edge_weight ON edges (weight)",
    "CREATE INDEX es_edge ON edge_sources (edge_id)",
    "CREATE INDEX es_source ON edge_sources (source_id)",
    "CREATE INDEX np_prefix ON node_prefixes (prefix_id)",
    "CREATE INDEX ef_feature ON edge_features (rel_id, direction, node_id)",
    "CREATE INDEX ef_node ON edge_features (node_id)",
    """
    CREATE MATERIALIZED VIEW ranked_features AS (
    SELECT ef.rel_id, ef.direction, ef.node_id, ef.edge_id, e.weight,
           row_number() OVER (
               PARTITION BY (ef.node_id, ef.rel_id, ef.direction)
               ORDER BY e.weight DESC, e.id
           ) AS rank
    FROM edge_features ef, edges e WHERE e.id=ef.edge_id
    ) WITH DATA
    """,
    "CREATE INDEX rf_node ON ranked_features (node_id)",
]


def run_commands(connection, commands):
    cursor = connection.cursor()
    for cmd in commands:
        print(cmd)
        cursor.execute(cmd)
    connection.commit()


def create_tables(connection):
    run_commands(connection, TABLES)


def create_indices(connection):
    run_commands(connection, INDICES)

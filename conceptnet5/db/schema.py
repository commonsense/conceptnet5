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

    """
    CREATE TABLE slot_lookup AS
        SELECT e.id AS edge_id, p.prefix_id AS prefix_id, 'start' AS slot,
               e.weight AS weight
        FROM edges e, node_prefixes p
        WHERE p.node_id = e.start_id
    """,
    """
    INSERT INTO slot_lookup (
        SELECT e.id AS edge_id, p.prefix_id AS prefix_id, 'end' AS slot,
               e.weight AS weight
        FROM edges e, node_prefixes p
        WHERE p.node_id = e.end_id
    )
    """,
    """
    CREATE TABLE two_way_lookup AS
        SELECT e.id AS edge_id, p1.prefix_id AS node_prefix_id,
        p2.prefix_id AS other_prefix_id, e.weight AS weight,
        1 AS direction
        FROM edges e, node_prefixes p1, node_prefixes p2
        WHERE p1.node_id = e.start_id
          AND p2.node_id = e.end_id
    """,
    """
    INSERT INTO two_way_lookup (
        SELECT e.id AS edge_id, p1.prefix_id AS node_prefix_id,
        p2.prefix_id AS other_prefix_id, e.weight AS weight,
        -1 AS direction
        FROM edges e, node_prefixes p1, node_prefixes p2
        WHERE p1.node_id = e.end_id
          AND p2.node_id = e.start_id
    )
    """,
    "CREATE INDEX sl_edge ON slot_lookup (edge_id)",
    "CREATE INDEX sl_prefix ON slot_lookup (prefix_id)",
    "CREATE INDEX sl_weight ON slot_lookup (weight)",
    "CREATE INDEX twl_edge ON two_way_lookup (edge_id)",
    "CREATE INDEX twl_pair ON two_way_lookup (node_prefix_id, other_prefix_id)",
    "CREATE INDEX twl_weight ON two_way_lookup (weight)",
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

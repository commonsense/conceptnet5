TABLES = [
    "DROP TABLE IF EXISTS nodes",
    "DROP TABLE IF EXISTS edges",
    "DROP TABLE IF EXISTS edge_sources",
    "DROP TABLE IF EXISTS node_prefixes",
    """CREATE TABLE nodes (
        id     integer NOT NULL PRIMARY KEY,
        uri    text NOT NULL UNIQUE
    )""",
    """CREATE TABLE edges (
        id             integer NOT NULL PRIMARY KEY,
        uri            text NOT NULL UNIQUE,
        relation_id    integer NOT NULL REFERENCES nodes (id),
        start_id       integer NOT NULL REFERENCES nodes (id),
        end_id         integer NOT NULL REFERENCES nodes (id),
        dataset_id     integer NOT NULL REFERENCES nodes (id),
        license_id     integer NOT NULL REFERENCES nodes (id),
        surface_text   text,
        start_text     text,
        end_text       text
    )""",
    """CREATE TABLE edge_sources (
        edge_id        integer NOT NULL REFERENCES edges (id),
        source_id      integer NOT NULL REFERENCES nodes (id),
        UNIQUE (edge_id, source_id)
    )
    """,
    """CREATE TABLE node_prefixes (
        node_id        integer NOT NULL REFERENCES nodes (id),
        prefix_id      integer NOT NULL REFERENCES nodes (id),
        UNIQUE (node_id, prefix_id)
    )
    """
]

INDICES = [
    "CREATE INDEX edge_relation ON nodes (relation_id)",
    "CREATE INDEX edge_start ON edges (start_id)",
    "CREATE INDEX edge_end ON edges (end_id)",
    "CREATE INDEX edge_dataset ON edges (dataset_id)",
    "CREATE INDEX edge_license ON edges (license_id)",
    "CREATE INDEX es_edge ON edge_sources (edge_id)",
    "CREATE INDEX es_source ON edge_sources (source_id)",
    "CREATE INDEX np_node ON node_prefixes (node_id)",
    "CREATE INDEX np_prefix ON node_prefixes (prefix_id)"
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

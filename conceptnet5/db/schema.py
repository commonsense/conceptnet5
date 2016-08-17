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
        dataset_id     integer NOT NULL REFERENCES nodes (id),
        license_id     integer NOT NULL REFERENCES nodes (id),
        weight         real,
        source_data    text,
        surface_text   text,
        start_text     text,
        end_text       text
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
    "CREATE INDEX edge_dataset ON edges (dataset_id)",
    "CREATE INDEX edge_license ON edges (license_id)",
    "CREATE INDEX es_edge ON edge_sources (edge_id)",
    "CREATE INDEX es_source ON edge_sources (source_id)",
    "CREATE INDEX np_node ON node_prefixes (node_id)",
    "CREATE INDEX np_prefix ON node_prefixes (prefix_id)"
]


VIEWS = [
    """
    CREATE VIEW edge_prefix_view AS
    SELECT e.id AS id, 1 AS direction,
        n0.uri AS rel_uri, n1.uri as start_uri, n2.uri as end_uri,
        np1.uri AS start_prefix, np2.uri AS end_prefix,
        np1.uri AS node_prefix, np2.uri AS other_prefix,
        nd.uri AS dataset_uri, nlic.uri AS license_uri,
        e.uri, e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
        FROM nodes n0, nodes n1, nodes n2, nodes np1, nodes np2, nodes nd, nodes nlic,
            edges e, node_prefixes p1, node_prefixes p2
        WHERE e.relation_id=n0.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND e.dataset_id=nd.id
        AND e.license_id=nlic.id
        AND n1.id=p1.node_id AND p1.prefix_id=np1.id
        AND n2.id=p2.node_id AND p2.prefix_id=np2.id
    UNION ALL
    SELECT e.id AS id, -1 AS direction,
        n0.uri AS rel_uri, n1.uri as start_uri, n2.uri as end_uri,
        np1.uri AS start_prefix, np2.uri AS end_prefix,
        np2.uri AS node_prefix, np1.uri AS other_prefix,
        nd.uri AS dataset_uri, nlic.uri AS license_uri,
        e.uri, e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
        FROM nodes n0, nodes n1, nodes n2, nodes np1, nodes np2, nodes nd, nodes nlic,
            edges e, node_prefixes p1, node_prefixes p2
        WHERE e.relation_id=n0.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND e.dataset_id=nd.id
        AND e.license_id=nlic.id
        AND n1.id=p1.node_id AND p1.prefix_id=np1.id
        AND n2.id=p2.node_id AND p2.prefix_id=np2.id;
    """,
    """
    CREATE VIEW edge_view AS
    SELECT e.id AS id, 1 AS direction,
        n0.uri AS rel_uri, n1.uri as start_uri, n2.uri as end_uri,
        n1.uri AS node_uri, n2.uri AS other_uri,
        nd.uri AS dataset_uri, nlic.uri AS license_uri,
        e.uri, e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
        FROM nodes n0, nodes n1, nodes n2, nodes np1, nodes np2, nodes nd, nodes nlic,
            edges e, node_prefixes p1, node_prefixes p2
        WHERE e.relation_id=n0.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND e.dataset_id=nd.id
        AND e.license_id=nlic.id
        AND n1.id=p1.node_id AND p1.prefix_id=np1.id
        AND n2.id=p2.node_id AND p2.prefix_id=np2.id
    UNION ALL
    SELECT e.id AS id, -1 AS direction,
        n0.uri AS rel_uri, n1.uri as start_uri, n2.uri as end_uri,
        np1.uri AS start_prefix, np2.uri AS end_prefix,
        np2.uri AS node_prefix, np1.uri AS other_prefix,
        nd.uri AS dataset_uri, nlic.uri AS license_uri,
        e.uri, e.weight, e.source_data, e.surface_text, e.start_text, e.end_text
        FROM nodes n0, nodes n1, nodes n2, nodes np1, nodes np2, nodes nd, nodes nlic,
            edges e, node_prefixes p1, node_prefixes p2
        WHERE e.relation_id=n0.id
        AND e.start_id=n1.id
        AND e.end_id=n2.id
        AND e.dataset_id=nd.id
        AND e.license_id=nlic.id
        AND n1.id=p1.node_id AND p1.prefix_id=np1.id
        AND n2.id=p2.node_id AND p2.prefix_id=np2.id;
    """
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
    run_commands(connection, VIEWS)

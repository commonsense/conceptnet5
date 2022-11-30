TABLES = [
    "DROP MATERIALIZED VIEW IF EXISTS ranked_features",
    "DROP TABLE IF EXISTS edge_features",
    "DROP TABLE IF EXISTS edge_sources",
    "DROP TABLE IF EXISTS edges_gin",
    "DROP TABLE IF EXISTS node_prefixes",
    "DROP TABLE IF EXISTS edges",
    "DROP TABLE IF EXISTS nodes",
    "DROP TABLE IF EXISTS sources",
    "DROP TABLE IF EXISTS relations",
    """CREATE TABLE nodes (
        id     integer NOT NULL,
        uri    text NOT NULL
    )""",
    """CREATE TABLE sources (
        id     integer NOT NULL,
        uri    text NOT NULL
    )""",
    """CREATE TABLE relations (
        id        integer NOT NULL,
        uri       text NOT NULL,
        directed  bool NOT NULL
    )
    """,
    """CREATE TABLE edges (
        id             integer NOT NULL,
        uri            text NOT NULL,
        relation_id    integer NOT NULL,
        start_id       integer NOT NULL,
        end_id         integer NOT NULL,
        weight         real NOT NULL,
        data           jsonb NOT NULL
    )
    """,
    """CREATE TABLE edges_gin (
        edge_id   integer NOT NULL,
        weight    real NOT NULL,
        data      jsonb NOT NULL
    )
    """,
    """CREATE TABLE edge_features (
        rel_id    integer NOT NULL,
        direction integer NOT NULL,
        node_id   integer NOT NULL,
        edge_id   integer NOT NULL
    )
    """,
]

INDICES = [
    "ALTER TABLE nodes ADD PRIMARY KEY (id)",
    "ALTER TABLE sources ADD PRIMARY KEY (id)",
    "ALTER TABLE relations ADD PRIMARY KEY (id)",
    "ALTER TABLE edges ADD PRIMARY KEY (id)",
    "ALTER TABLE edges ADD FOREIGN KEY (relation_id) REFERENCES relations (id)",
    "ALTER TABLE edges ADD FOREIGN KEY (start_id) REFERENCES nodes (id)",
    "ALTER TABLE edges ADD FOREIGN KEY (end_id) REFERENCES nodes (id)",
    "ALTER TABLE edges_gin ADD FOREIGN KEY (edge_id) REFERENCES edges (id)",
    "ALTER TABLE edge_features ADD FOREIGN KEY (rel_id) REFERENCES relations (id)",
    "ALTER TABLE edge_features ADD FOREIGN KEY (node_id) REFERENCES nodes (id)",
    "ALTER TABLE edge_features ADD FOREIGN KEY (edge_id) REFERENCES edges (id)",
    "ALTER TABLE nodes ADD CONSTRAINT nodes_unique_uri UNIQUE (uri)",
    "ALTER TABLE sources ADD CONSTRAINT sources_unique_uri UNIQUE (uri)",
    "ALTER TABLE edges ADD CONSTRAINT edges_unique_uri UNIQUE (uri)",
    "ALTER TABLE relations ADD CONSTRAINT relations_unique_uri UNIQUE (uri)",
    "CREATE INDEX edge_relation ON edges (relation_id)",
    "CREATE INDEX edge_start ON edges (start_id)",
    "CREATE INDEX edge_end ON edges (end_id)",
    "CREATE INDEX edge_weight ON edges (weight)",
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
    "CREATE INDEX edges_gin_index ON edges_gin USING gin (data jsonb_path_ops)",
]

SIMPLIFIED_EDGES_VIEW = [
    """
    CREATE MATERIALIZED VIEW simplified_edges AS (
        SELECT 
            me.edge_id as edge_id, 
            ed.uri as edge_uri, 
            s.uri as start_uri, 
            e.uri as end_uri, 
            r.uri as rel_uri, 
            ed.data->>'dataset' as dataset,
            ed.weight 
        FROM edges_gin me
		INNER JOIN edges ed ON me.edge_id = ed.id
        INNER JOIN nodes s on ed.start_id = s.id
        INNER JOIN nodes e on ed.end_id = e.id
        INNER JOIN relations r on ed.relation_id = r.id
	) WITH DATA
    """,
]


def run_commands(connection, commands):
    with connection:
        with connection.cursor() as cursor:
            for cmd in commands:
                cursor.execute(cmd)

def create_tables(connection):
    run_commands(connection, TABLES)

def create_simplified_edges_view(connection):
    run_commands(connection, SIMPLIFIED_EDGES_VIEW)

def create_indices(connection):
    run_commands(connection, INDICES)

import psycopg2

from conceptnet5.db import config

_CONNECTIONS = {}


def get_db_connection(dbname=None):
    """
    Get a global connection to the ConceptNet PostgreSQL database.

    `dbname` specifies the name of the database in PostgreSQL.
    """
    if dbname is None:
        dbname = config.DB_NAME
    if dbname in _CONNECTIONS:
        return _CONNECTIONS[dbname]
    else:
        _CONNECTIONS[dbname] = _get_db_connection_inner(dbname)
        return _CONNECTIONS[dbname]


def _get_db_connection_inner(dbname):
    if config.DB_PASSWORD:
        conn = psycopg2.connect(
            dbname=dbname,
            user=config.DB_USERNAME,
            password=config.DB_PASSWORD,
            host=config.DB_HOSTNAME,
            port=config.DB_PORT
        )
    else:
        conn = psycopg2.connect(dbname=dbname)

    conn.autocommit = True
    psycopg2.paramstyle = 'named'
    return conn


def check_db_connection(dbname=None):
    """
    Raise an error early if we can't access the database. This is intended
    to be used at the start of the build script.

    The desired outcome is that we successfully make a connection (and then
    throw it away). If the DB is unavailable, this will raise an uncaught
    error.
    """
    if dbname is None:
        dbname = config.DB_NAME
    _get_db_connection_inner(dbname)

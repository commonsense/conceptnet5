import pg8000
import time
import sys
import os
from conceptnet5.db import config
from conceptnet5.util import get_data_filename

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
        for attempt in range(10):
            try:
                _CONNECTIONS[dbname] = _get_db_connection_inner(dbname)
                return _CONNECTIONS[dbname]
            except pg8000.InterfaceError:
                if attempt == 0:
                    print(
                        "Database %r is not available, retrying for 10 seconds" % dbname,
                        file=sys.stderr
                    )
                time.sleep(1)
        raise IOError(
            "Couldn't connect to database %r" % dbname
        )


def _get_db_connection_inner(dbname):
    if not config.DB_PASSWORD:
        conn = pg8000.connect(
            user=config.DB_USERNAME,
            unix_sock=config.DB_SOCKET,
            database=dbname
        )
    else:
        conn = pg8000.connect(
            user=config.DB_USERNAME,
            password=config.DB_PASSWORD,
            host=config.DB_HOSTNAME,
            port=config.DB_PORT,
            database=dbname
        )

    pg8000.paramstyle = 'named'
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


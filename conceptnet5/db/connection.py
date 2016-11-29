import pg8000
import time
import sys
import os
from conceptnet5.db import config
from conceptnet5.util import get_data_filename

_CONNECTIONS = {}


def get_db_connection(dbname=None, building=False):
    """
    Get a global connection to the ConceptNet PostgreSQL database.

    `dbname` specifies the name of the database in PostgreSQL.
    `building` specifies whether it's okay for the DB to not exist
    (set it to True at build time).
    """
    if not building and not os.access(get_data_filename('psql/done'), os.F_OK):
        raise IOError("The ConceptNet database has not been built.")
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
                        "Database %r at %s:%s is not available, retrying for 10 seconds"
                        % (dbname, config.DB_HOSTNAME, config.DB_PORT),
                        file=sys.stderr
                    )
                time.sleep(1)
        raise IOError(
            "Couldn't connect to database %r at %s:%s" %
            (dbname, config.DB_HOSTNAME, config.DB_PORT)
        )


def _get_db_connection_inner(dbname):
    conn = pg8000.connect(
        user=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_HOSTNAME,
        port=config.DB_PORT,
        database=dbname
    )
    pg8000.paramstyle = 'named'
    return conn

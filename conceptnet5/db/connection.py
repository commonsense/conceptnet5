import pg8000
from conceptnet5.db import config

_CONNECTIONS = {}


def get_db_connection(dbname=None):
    """
    Get a global connection to the ConceptNet PostgreSQL database.
    """
    if dbname is None:
        dbname = config.DB_NAME
    if dbname in _CONNECTIONS:
        return _CONNECTIONS[dbname]
    else:
        try:
            _CONNECTIONS[dbname] = pg8000.connect(
                user=config.DB_USERNAME,
                password=config.DB_PASSWORD,
                host=config.DB_HOSTNAME,
                port=config.DB_PORT,
                database=dbname
            )
            pg8000.paramstyle = 'named'
            return _CONNECTIONS[dbname]
        except pg8000.InterfaceError:
            raise IOError(
                "Couldn't connect to database %r at %s:%s" %
                (dbname, config.DB_HOSTNAME, config.DB_PORT)
            )
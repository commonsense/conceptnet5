import pg8000
from conceptnet5.db import config

_CONNECTION = None


def get_db_connection():
    """
    Get a global connection to the ConceptNet PostgreSQL database.
    """
    global _CONNECTION
    if _CONNECTION is not None:
        return _CONNECTION
    else:
        _CONNECTION = pg8000.connect(
            user=config.DB_USERNAME,
            password=config.DB_PASSWORD,
            host=config.DB_HOSTNAME,
            port=config.DB_PORT,
            database=config.DB_NAME
        )
        pg8000.paramstyle = 'named'
        return _CONNECTION

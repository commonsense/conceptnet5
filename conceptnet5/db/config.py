"""
You can configure how ConceptNet accesses its database with the following
environment variables:

    CONCEPTNET_DB_USER - the username to connect to the DB with
    CONCEPTNET_DB_PASSWORD - the DB password, if necessary
    CONCEPTNET_DB_HOSTNAME - the host to connect to (default "localhost")
    CONCEPTNET_DB_PORT - the port number to connect to (default 5432)
    CONCEPTNET_DB_NAME - the database name to use (default "conceptnet5")
"""
import os

DB_USERNAME = os.environ.get('CONCEPTNET_DB_USER', os.environ.get('USER', 'postgres'))
DB_PASSWORD = os.environ.get('CONCEPTNET_DB_PASSWORD', '')
DB_HOSTNAME = os.environ.get('CONCEPTNET_DB_HOSTNAME', 'localhost')
DB_PORT = int(os.environ.get('CONCEPTNET_DB_PORT', '5432'))
DB_NAME = os.environ.get('CONCEPTNET_DB_NAME', 'conceptnet5')

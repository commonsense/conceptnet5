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

DB_USERNAME = os.environ.get('CONCEPTNET_DB_USER', os.environ.get('USER', 'www-data'))
DB_PASSWORD = os.environ.get('CONCEPTNET_DB_PASSWORD')

if DB_PASSWORD is None:
    DB_USERPASS = DB_USERNAME
else:
    DB_USERPASS = '{}:{}'.format(DB_USERNAME, DB_PASSWORD)


DB_CONNECTION = 'postgresql+{engine}://{userpass}@{host}:{port}/{dbname}'.format(
    engine='pg8000',
    userpass=DB_USERPASS,
    host=os.environ.get('CONCEPTNET_DB_HOSTNAME', 'localhost'),
    port=os.environ.get('CONCEPTNET_DB_PORT', '5432'),
    dbname=os.environ.get('CONCEPTNET_DB_NAME', 'conceptnet5')
)

from conceptnet5.uri import uri_prefixes
import sqlite3
import struct
from hashlib import sha1


class SQLiteWriter(object):
    """
    A very simple abstraction over some SQLite writing operations.
    Emphatically not an ORM.
    """
    schema = []
    drop_schema = []

    def __init__(self, filename, clear=False):
        self.db = None
        self.filename = filename
        self.initialize_db(clear)

    def initialize_db(self, clear=False):
        """
        Create the DB with the appropriate schema. If `clear` is True, any
        existing file with this name will be removed. If it is False,
        it will reuse any existing database with this name.
        """
        if self.db is not None:
            self.db.close()

        self.db = sqlite3.connect(self.filename)

        c = self.db.cursor()
        if clear:
            for cmd in self.drop_schema:
                c.execute(cmd)

        c = self.db.cursor()
        for cmd in self.schema:
            c.execute(cmd)

    def close(self):
        self.db.commit()
        self.db.close()

    def commit(self):
        self.db.commit()


class TitleDBWriter(SQLiteWriter):
    schema = [
        "CREATE TABLE IF NOT EXISTS titles (language text, title text)",
        "CREATE UNIQUE INDEX IF NOT EXISTS titles_uniq ON titles (language, title)"
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS titles"
    ]

    def add(self, language, title):
        c = self.db.cursor()
        c.execute(
            "INSERT OR IGNORE INTO titles (language, title) VALUES (?, ?)",
            (language, title)
        )


def minihash(prefix):
    """
    Get a 32-bit SHA1 hash of the given prefix string, which can be stored
    compactly in the DB as an integer.
    """
    dbytes = sha1(prefix.encode('utf-8')).digest()[:4]
    return struct.unpack('>i', dbytes)[0]


class EdgeIndexWriter(SQLiteWriter):
    schema = [
        """CREATE TABLE IF NOT EXISTS assertions (
            id integer PRIMARY KEY,
            uri text UNIQUE,
            filename text,
            offset integer
        )""",
        """CREATE TABLE IF NOT EXISTS prefixes (
            prefixhash integer,
            assertion_id integer,
            weight real,
            complete bool
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS prefix_uniq on prefixes (prefixhash, assertion_id)",
        "CREATE INDEX IF NOT EXISTS prefix_lookup on prefixes (prefixhash ASC, weight DESC)",
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS assertions",
        "DROP TABLE IF EXISTS prefixes"
    ]

    def add(self, assertion, filename, offset):
        assertion_id = self.add_uri(assertion, filename, offset)
        for field in ('rel', 'start', 'end', 'dataset', 'license'):
            self.add_prefixes(assertion_id, assertion[field], assertion['weight'])
        for source in assertion['sources']:
            self.add_prefixes(assertion_id, source, assertion['weight'])

    def add_uri(self, assertion, filename, offset):
        c = self.db.cursor()
        c.execute(
            "INSERT OR REPLACE INTO ASSERTIONS (uri, filename, offset) "
            "VALUES (?, ?, ?)",
            (assertion['uri'], filename, offset)
        )
        return c.lastrowid

    def add_prefixes(self, assertion_id, path, weight):
        c = self.db.cursor()
        for prefix in uri_prefixes(path):
            complete = (prefix == path)
            prefixhash = minihash(prefix)
            c.execute(
                "INSERT OR IGNORE INTO prefixes "
                "(prefixhash, assertion_id, weight, complete) "
                "VALUES (?, ?, ?, ?)",
                (prefixhash, assertion_id, weight, complete)
            )

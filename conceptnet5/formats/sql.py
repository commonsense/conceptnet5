from conceptnet5.uri import uri_prefixes
import sqlite3
import struct
import json
import os
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

    def transaction(self):
        """
        Return a context manager that wraps commands in a transaction --
        which is the same as the connection object.
        """
        return self.db

    def close(self):
        self.db.close()


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


def minihash(index):
    """
    Get a 32-bit SHA1 hash of the given index string, which can be stored
    compactly in the DB as an integer.
    """
    dbytes = sha1(index.encode('utf-8')).digest()[:4]
    return struct.unpack('>i', dbytes)[0]


INT_LIMIT = 2 ** 63 - 1


def edge_id_hash(edge_id):
    """
    Represent the first 16 digits of an edge ID as a 64-bit integer.
    """
    val = int(edge_id[3:19], 16)
    if val >= INT_LIMIT:
        return val - INT_LIMIT * 2
    else:
        return val


class EdgeIndexWriter(SQLiteWriter):
    schema = [
        """CREATE TABLE IF NOT EXISTS assertions (
            id integer PRIMARY KEY,
            filename text,
            offset integer
        ) WITHOUT ROWID""",
        """CREATE TABLE IF NOT EXISTS text_index (
            indexhash integer,
            assertion_id integer,
            weight real,
            complete bool
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS prefix_uniq on text_index (indexhash, assertion_id)",
        "CREATE INDEX IF NOT EXISTS prefix_lookup on text_index (indexhash ASC, weight DESC)",
        "PRAGMA synchronous = OFF",
        "PRAGMA journal_mode = MEMORY"
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS assertions",
        "DROP TABLE IF EXISTS text_index"
    ]

    def add(self, assertion, filename, offset):
        assertion_id = self.add_uri(assertion, filename, offset)
        for field in ('uri', 'rel', 'start', 'end', 'dataset'):
            self.add_prefixes(assertion_id, assertion[field], assertion['weight'])
        for source in assertion['sources']:
            self.add_prefixes(assertion_id, source, assertion['weight'])
        for feature in assertion['features']:
            self.add_string_index(assertion_id, feature, assertion['weight'])

    def add_uri(self, assertion, filename, offset):
        assertion_id = edge_id_hash(assertion['id'])
        c = self.db.cursor()
        c.execute(
            "INSERT OR REPLACE INTO ASSERTIONS (id, filename, offset) "
            "VALUES (?, ?, ?)",
            (assertion_id, filename, offset)
        )
        return assertion_id

    def add_prefixes(self, assertion_id, path, weight):
        c = self.db.cursor()
        for prefix in uri_prefixes(path):
            complete = (prefix == path)
            indexhash = minihash(prefix)
            c.execute(
                "INSERT OR IGNORE INTO text_index "
                "(indexhash, assertion_id, weight, complete) "
                "VALUES (?, ?, ?, ?)",
                (indexhash, assertion_id, weight, complete)
            )

    def add_string_index(self, assertion_id, string, weight):
        c = self.db.cursor()
        complete = True
        indexhash = minihash(string)
        c.execute(
            "INSERT OR IGNORE INTO text_index "
            "(indexhash, assertion_id, weight, complete) "
            "VALUES (?, ?, ?, ?)",
            (indexhash, assertion_id, weight, complete)
        )


class EdgeIndexReader(object):
    def __init__(self, filename, edge_directory):
        self.filename = filename
        self.edge_directory = edge_directory
        self.open_file_cache = {}
        self.db = sqlite3.connect(filename)

    def lookup_index(self, index, complete=False, limit=20):
        mh = minihash(index)
        c = self.db.cursor()
        if complete:
            c.execute(
                "SELECT a.filename, a.offset from assertions a, text_index t "
                "WHERE t.assertion_id = a.id AND t.indexhash = ? "
                "AND complete = true ORDER BY t.weight DESC",
                (mh,)
            )
        else:
            c.execute(
                "SELECT a.filename, a.offset from assertions a, text_index t "
                "WHERE t.assertion_id = a.id AND t.indexhash = ? "
                "ORDER BY t.weight DESC",
                (mh,)
            )

        count = 0
        while True:
            rows = c.fetchmany()
            if not rows:
                return
            for (filename, offset) in rows:
                yield self.get_assertion(filename, offset)
                count += 1
                if count >= limit:
                    return

    def get_assertion(self, filename, offset):
        if filename in self.open_file_cache:
            fileobj = self.open_file_cache[filename]
        else:
            fileobj = open(os.path.join(self.edge_directory, filename), 'rb')
            self.open_file_cache[filename] = fileobj
        fileobj.seek(offset)
        bline = fileobj.readline()
        line = bline.decode('utf-8').strip()
        return json.loads(line)

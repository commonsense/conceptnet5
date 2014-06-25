from conceptnet5.uri import uri_prefixes
import sqlite3
import struct
import json
import os
import re
from hashlib import sha1

INT_LIMIT = 2 ** 63 - 1
SURFACE_TEXT_RE = re.compile(r'\[\[(.*?)\]\]')


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
        """CREATE TABLE IF NOT EXISTS edges (
            id integer PRIMARY KEY,
            filename text,
            offset integer
        ) WITHOUT ROWID""",
        """CREATE TABLE IF NOT EXISTS text_index (
            queryhash integer,
            edge_id integer,
            weight real,
            complete bool
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS prefix_uniq on text_index (queryhash, edge_id)",
        "CREATE INDEX IF NOT EXISTS prefix_lookup on text_index (queryhash ASC, weight DESC)",
        "PRAGMA synchronous = OFF",
        "PRAGMA journal_mode = MEMORY"
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS edges",
        "DROP TABLE IF EXISTS text_index"
    ]

    def add(self, edge, filename, offset):
        edge_id = self.add_edge(edge, filename, offset)
        for field in ('uri', 'rel', 'start', 'end', 'dataset'):
            self.add_prefixes(edge_id, edge[field], edge['weight'])
        for source in edge['sources']:
            self.add_prefixes(edge_id, source, edge['weight'])
        for feature in edge['features']:
            self.add_string_index(edge_id, feature, edge['weight'])
        if 'surfaceText' in edge:
            for text in SURFACE_TEXT_RE.findall(edge['surfaceText']):
                self.add_string_index(edge_id, text, edge['weight'])

    def add_edge(self, edge, filename, offset):
        edge_id = edge_id_hash(edge['id'])
        c = self.db.cursor()
        c.execute(
            "INSERT OR REPLACE INTO edges (id, filename, offset) "
            "VALUES (?, ?, ?)",
            (edge_id, filename, offset)
        )
        return edge_id

    def add_prefixes(self, edge_id, path, weight):
        c = self.db.cursor()
        for prefix in uri_prefixes(path):
            complete = (prefix == path)
            queryhash = minihash(prefix)
            c.execute(
                "INSERT OR IGNORE INTO text_index "
                "(queryhash, edge_id, weight, complete) "
                "VALUES (?, ?, ?, ?)",
                (queryhash, edge_id, weight, complete)
            )

    def add_string_index(self, edge_id, string, weight):
        c = self.db.cursor()
        complete = True
        queryhash = minihash(string)
        c.execute(
            "INSERT OR IGNORE INTO text_index "
            "(queryhash, edge_id, weight, complete) "
            "VALUES (?, ?, ?, ?)",
            (queryhash, edge_id, weight, complete)
        )


class EdgeIndexReader(object):
    def __init__(self, filename, edge_dir):
        self.filename = filename
        self.edge_dir = edge_dir
        self.open_file_cache = {}
        self.db = sqlite3.connect(filename)

    def lookup(self, query, complete=False, limit=None, offset=0):
        if limit is None:
            pseudo_limit = 1000000000
        else:
            pseudo_limit = limit

        mh = minihash(query)
        c = self.db.cursor()
        complete_req = ''
        if complete:
            complete_req = ' AND complete = true'

        # If your hair is standing on end when you see "%s" in a SQL
        # expression, I don't blame you. But the only thing being substituted
        # this way is the `complete_req` defined just above. Don't worry,
        # there's no room for a SQL injection.
        c.execute(
            "SELECT e.filename, e.offset from edges e, text_index t "
            "WHERE t.edge_id = e.id AND t.queryhash = ? "
            "%s ORDER BY t.weight DESC LIMIT ? OFFSET ?" % complete_req,
            (mh, pseudo_limit, offset)
        )
        if limit is not None:
            rows = c.fetchall()
            return [self.get_edge(filename, offset)
                    for (filename, offset) in rows]
        else:
            return self.edge_iterator(c)

    def edge_iterator(self, cursor):
        while True:
            rows = cursor.fetchmany()
            if not rows:
                return
            for (filename, offset) in rows:
                yield self.get_edge(filename, offset)

    def get_edge(self, filename, offset):
        if filename in self.open_file_cache:
            fileobj = self.open_file_cache[filename]
        else:
            fileobj = open(os.path.join(self.edge_dir, filename), 'rb')
            self.open_file_cache[filename] = fileobj
        fileobj.seek(offset)
        bline = fileobj.readline()
        line = bline.decode('utf-8').strip()
        return json.loads(line)

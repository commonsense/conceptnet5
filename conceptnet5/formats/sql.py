from __future__ import print_function, unicode_literals
from conceptnet5.uri import uri_prefixes
from conceptnet5.formats.msgpack_stream import encoding
from msgpack import Unpacker
import sqlite3
import struct
import os
import re
import random
from hashlib import md5

INT_LIMIT = 2 ** 63 - 1
SURFACE_TEXT_RE = re.compile(r'\[\[(.*?)\]\]')

# Import apsw if we can.
try:
    import apsw
except ImportError:
    apsw = None


class SQLiteWriter(object):
    """
    A very simple abstraction over some SQLite writing operations.
    Emphatically not an ORM.
    """
    schema = []
    drop_schema = []

    def __init__(self, filename, clear=False, allow_apsw=False):
        self.db = None
        self.filename = filename
        self.enable_apsw = False
        if allow_apsw:
            if apsw is None:
                print("You asked to use APSW to write the database, but I "
                      "couldn't import it. Falling back on sqlite3.")
            else:
                self.enable_apsw = True
        self.initialize_db(clear)

    def _connect(self, filename):
        """
        Get a connection to the database.
        """
        if self.enable_apsw:
            # Get an in-memory SQLite 3 connection. (It will only be written to
            # the given filename when the database is closed.)
            return apsw.Connection(':memory:')
        else:
            # We're using the sqlite3 built into Python, so we'll be writing
            # to disk the whole time.
            return sqlite3.connect(filename)

    def initialize_db(self, clear=False):
        """
        Create the DB with the appropriate schema. If `clear` is True, any
        existing file with this name will be removed. If it is False,
        it will reuse any existing database with this name.
        """
        if self.db is not None:
            self.db.close()

        self.db = self._connect(self.filename)

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
        if self.enable_apsw:
            # We opened the DB in memory before. Now we need to write it to
            # the disk.
            target = apsw.Connection(self.filename)
            print("Writing to %s:" % self.filename)
            with target.backup('main', self.db, 'main') as backup:
                while not backup.done:
                    backup.step(100)
                    print('\t%s/%s remaining  ' % (backup.remaining, backup.pagecount),
                          end='\r', flush=True)
            print()
            target.close()
        else:
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
    dbytes = md5(index.encode('utf-8')).digest()[:4]
    return struct.unpack(str('>i'), dbytes)[0]


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
        """CREATE TABLE IF NOT EXISTS text_index (
            queryhash integer,
            filenum integer,
            offset integer,
            weight real,
            complete bool
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS prefix_uniq on text_index (queryhash, filenum, offset)",
        "CREATE INDEX IF NOT EXISTS prefix_lookup on text_index (queryhash ASC, weight DESC)",
        "PRAGMA synchronous = OFF",
        "PRAGMA journal_mode = OFF"
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS text_index"
    ]

    def __init__(self, filename, shard_num, nshards, clear=False,
                 allow_apsw=False):
        SQLiteWriter.__init__(self, filename, clear=clear,
                              allow_apsw=allow_apsw)
        self.shard_num = shard_num
        self.nshards = nshards

    def add(self, edge, filenum, offset):
        for field in ('uri', 'rel', 'start', 'end', 'dataset'):
            self.add_prefixes(filenum, offset, edge[field], edge['weight'])
        for source in edge['sources']:
            self.add_prefixes(filenum, offset, source, edge['weight'])
        for feature in edge['features']:
            self.add_string_index(filenum, offset, feature, edge['weight'])
        ## We might not actually want to index by surface text. If we want to
        ## sort edges with different surface texts, we could also do it at
        ## lookup time.
        #
        #if edge.get('surfaceText'):
        #    for text in SURFACE_TEXT_RE.findall(edge['surfaceText']):
        #        self.add_string_index(filenum, offset, text, edge['weight'])

    def add_prefixes(self, filenum, offset, path, weight):
        for prefix in uri_prefixes(path):
            complete = (prefix == path)
            queryhash = minihash(prefix)
            shard = queryhash % self.nshards
            if shard == self.shard_num:
                c = self.db.cursor()
                c.execute(
                    "INSERT OR IGNORE INTO text_index "
                    "(queryhash, filenum, offset, weight, complete) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (queryhash, filenum, offset, weight, complete)
                )

    def add_string_index(self, filenum, offset, string, weight):
        complete = True
        queryhash = minihash(string)
        shard = queryhash % self.nshards
        if shard == self.shard_num:
            c = self.db.cursor()
            c.execute(
                "INSERT OR IGNORE INTO text_index "
                "(queryhash, filenum, offset, weight, complete) "
                "VALUES (?, ?, ?, ?, ?)",
                (queryhash, filenum, offset, weight, complete)
            )


class EdgeIndexReader(object):
    def __init__(self, filename, edge_dir, nshards=8):
        self.filename = filename
        self.edge_dir = edge_dir
        self.open_file_cache = {}
        self.dbs = {}
        self.nshards = nshards
        self._connect()

    def _connect(self):
        for i in range(self.nshards):
            filename = '%s.%d' % (self.filename, i)
            self.dbs[i] = sqlite3.connect(filename)

    def lookup(self, query, complete=False, limit=None, offset=0):
        if limit is None:
            pseudo_limit = 1000000000
        else:
            pseudo_limit = limit

        mh = minihash(query)
        shard = mh % self.nshards
        c = self.dbs[shard].cursor()
        complete_req = ''
        if complete:
            complete_req = ' AND complete = true'

        # If your hair is standing on end when you see "%s" in a SQL
        # expression, I don't blame you. But the only thing being substituted
        # this way is the `complete_req` defined just above. Don't worry,
        # there's no room for a SQL injection.
        c.execute(
            "SELECT filenum, offset from text_index "
            "WHERE queryhash = ? "
            "%s ORDER BY weight DESC LIMIT ? OFFSET ?" % complete_req,
            (mh, pseudo_limit, offset)
        )
        return self.edge_iterator(c)

    def edge_iterator(self, cursor):
        while True:
            rows = cursor.fetchmany(size=50)
            if not rows:
                return
            for (filenum, offset) in rows:
                yield self.get_edge(filenum, offset)

    def get_edge(self, filenum, offset):
        fileobj = self.get_file(filenum)
        fileobj.seek(offset)
        unpacker = Unpacker(fileobj, encoding=encoding)
        return unpacker.unpack()

    def get_file(self, filenum):
        if filenum in self.open_file_cache:
            return self.open_file_cache[filenum]
        else:
            filename = 'part_%02d.msgpack' % filenum
            path = os.path.join(self.edge_dir, filename)
            size = os.path.getsize(path)
            fileobj = open(path, 'rb')
            self.open_file_cache[filenum] = fileobj
            return fileobj

    def random(self):
        hashval = random.randrange(-2**31, 2**31)
        shard = hashval % self.nshards
        c = self.dbs[shard].cursor()
        offset = random.randrange(0, 100)
        rows = []
        while not rows:
            c.execute(
                "SELECT filenum, offset from text_index "
                "WHERE queryhash >= ? "
                "ORDER BY queryhash LIMIT 1 OFFSET ?",
                (hashval, offset)
            )
            rows = c.fetchall()

        filenum, offset = rows[0]
        return self.get_edge(filenum, offset)

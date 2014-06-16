from conceptnet5.uri import uri_prefixes
import sqlite3
import json


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


class EdgeIndexWriter(SQLiteWriter):
    schema = [
        """CREATE TABLE IF NOT EXISTS assertions (
            id integer PRIMARY KEY,
            uri text UNIQUE,
            value text
        )""",
        """CREATE TABLE IF NOT EXISTS prefixes (
            prefix text,
            assertion_id integer,
            weight real,
            complete bool
        )""",
        "CREATE UNIQUE INDEX IF NOT EXISTS prefix_uniq on prefixes (prefix, assertion_id)",
        "CREATE INDEX IF NOT EXISTS prefix_lookup on prefixes (prefix ASC, weight DESC)",
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS assertions",
        "DROP TABLE IF EXISTS prefixes"
    ]

    def add(self, assertion):
        assertion_id = self.add_uri(assertion)
        for field in ('uri', 'rel', 'start', 'end', 'dataset', 'license'):
            self.add_prefixes(assertion_id, assertion[field], assertion['weight'])
        for source in assertion['sources']:
            self.add_prefixes(assertion_id, source, assertion['weight'])

    def add_uri(self, assertion):
        c = self.db.cursor()
        c.execute(
            "INSERT OR REPLACE INTO ASSERTIONS (uri, value) VALUES (?, ?)",
            (assertion['uri'], json.dumps(assertion, ensure_ascii=False))
        )
        return c.lastrowid

    def add_prefixes(self, assertion_id, path, weight):
        c = self.db.cursor()
        for prefix in uri_prefixes(path):
            complete = (prefix == path)
            c.execute(
                "INSERT OR IGNORE INTO prefixes "
                "(prefix, assertion_id, weight, complete) "
                "VALUES (?, ?, ?, ?)",
                (prefix, assertion_id, weight, complete)
            )

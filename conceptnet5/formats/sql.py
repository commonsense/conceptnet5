import sqlite3


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
        "CREATE TABLE IF NOT EXISTS titles (language text, title text);",
        "CREATE UNIQUE INDEX IF NOT EXISTS titles_uniq ON titles (language, title);"
    ]
    drop_schema = [
        "DROP TABLE IF EXISTS titles;"
    ]

    def add(self, language, title):
        c = self.db.cursor()
        c.execute(
            "INSERT OR IGNORE INTO titles (language, title) VALUES (?, ?)",
            (language, title)
        )


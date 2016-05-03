from conceptnet5.formats.json_stream import read_json_stream
import sqlite3
import pathlib


def prepare_db(inputs, dbfile):
    db = sqlite3.connect(dbfile)
    make_tables(db)
    try:
        for filename in inputs:
            filepath = pathlib.Path(filename)
            file_language = filepath.name.split('.')[0]
            for item in read_json_stream(filename):
                if 'language' in item:
                    add_title(
                        db, file_language, item['language'], item['title']
                    )
                    print(item['language'], item['title'])
                elif 'rel' in item and item['rel'].startswith('form/'):
                    form_name = item['rel'][5:]
                    tfrom = item['from']
                    tto = item['to']
                    pos = tfrom.get('pos', '')
                    add_form(
                        db, file_language, tfrom['language'],
                        tfrom['text'], pos, tto['text'], form_name
                    )
    finally:
        db.close()


def make_tables(db):
    db.execute("CREATE TABLE titles (id integer primary key, site_language text, language text, title text)")
    db.execute("CREATE INDEX titles_search ON titles (language, title)")

    db.execute("CREATE TABLE forms (id integer primary key, site_language text, language text, word text, pos text, root text, form text)")
    db.execute("CREATE INDEX forms_search ON forms (language, word)")


def add_title(db, file_language, language, title):
    db.execute(
        "INSERT INTO titles (site_language, language, title) "
        "VALUES (?, ?, ?)",
        (file_language, language, title)
    )


def add_form(db, file_language, language, word, pos, root, form):
    db.execute(
        "INSERT INTO forms (site_language, language, word, pos, root, form) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (file_language, language, word, pos, root, form)
    )

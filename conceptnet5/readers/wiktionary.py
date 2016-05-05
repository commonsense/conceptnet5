from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.uri import Licenses
import sqlite3
import pathlib
import os
import re
import langcodes
from langcodes.tag_parser import LanguageTagError


PARSER_RULE = '/s/rule/wikiparsec/1'


def prepare_db(inputs, dbfile):
    """
    Build a SQLite database that extracts some information from our parsed
    versions of Wiktionary. This is information that is needed by later reader
    steps, such as which words are known in which languages, and which words
    are forms of other words.
    """
    # If the database already exists, delete it first
    try:
        os.unlink(dbfile)
    except FileNotFoundError:
        pass

    db = sqlite3.connect(dbfile)
    make_tables(db)
    try:
        for filename in inputs:
            filepath = pathlib.Path(filename)
            file_language = filepath.name.split('.')[0]
            for item in read_json_stream(filename):
                if 'rel' in item:
                    tfrom = item['from']
                    tto = item['to']
                    if item['rel'] != 'definition':
                        if 'language' in tfrom and valid_language(tfrom['language']):
                            add_title(db, file_language, tfrom['language'], tfrom['text'])
                        if 'language' in tto and valid_language(tto['language']):
                            add_title(db, file_language, tto['language'], tto['text'])
                    if item['rel'].startswith('form/'):
                        form_name = item['rel'][5:]
                        pos = tfrom.get('pos', tto.get('pos', '?'))
                        language = tfrom.get('language', tto.get('language'))
                        if language is not None:
                            add_form(
                                db, file_language, language,
                                tfrom['text'], pos, tto['text'], form_name
                            )
            db.commit()
    finally:
        db.close()


# A regex that simple language codes will match. This is not the complete
# way that we check language codes, it's just a shortcut.
ALPHA3_RE = re.compile(r'^[a-z][a-z][a-z]?$')


def valid_language(code):
    if code == '' or code == 'und':
        return False
    if ALPHA3_RE.match(code):
        return True
    try:
        lcode = langcodes.get(code)
        return lcode.language is not None and len(lcode.language) <= 3
    except LanguageTagError:
        return False


def make_tables(db):
    db.execute("CREATE TABLE titles (id integer primary key, site_language text, language text, title text)")
    db.execute("CREATE UNIQUE INDEX titles_uniq ON titles (site_language, language, title)")
    db.execute("CREATE INDEX titles_search ON titles (language, title)")

    db.execute("CREATE TABLE forms (id integer primary key, site_language text, language text, word text, pos text, root text, form text)")
    db.execute("CREATE INDEX forms_search ON forms (language, word)")


def add_title(db, file_language, language, title):
    db.execute(
        "INSERT OR IGNORE INTO titles (site_language, language, title) "
        "VALUES (?, ?, ?)",
        (file_language, language, title)
    )


def add_form(db, file_language, language, word, pos, root, form):
    db.execute(
        "INSERT INTO forms (site_language, language, word, pos, root, form) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (file_language, language, word, pos, root, form)
    )


WIKT_RELATIONS = {
    "link": ("/r/RelatedTo", False),
    "related": ("/r/RelatedTo", False),
    "synonym": ("/r/Synonym", False),
    "antonym": ("/r/Antonym", False),
    "hypernym": ("/r/IsA", False),
    "holonym": ("/r/PartOf", False),
    "troponym": ("/r/MannerOf", True),
    "context": ("/r/HasContext", False),
    "derived": ("/r/DerivedFrom", True),
    "derived/etym": ("/r/EtymologicallyDerivedFrom", True),
    "form": ("/r/FormOf", False),
    "variant": ("/r/FormOf", True),
    "diminutive": ("/r/FormOf", True),
    "augmentative": ("/r/FormOf", True),
    "coordinate": ("/r/SimilarTo", False),
    "quasi-synonym": ("/r/SimilarTo", False),
    "translation": ("/r/TranslationOf", False),
    "definition": (None, False)
}


def transform_relation(rel):
    if rel.startswith('form/'):
        return "/r/FormOf", False
    else:
        return WIKT_RELATIONS[rel]


def transform_term(termdata, assumed_languages, db):
    text = termdata['text']
    language = termdata.get('language')
    if language is None:
        language = disambiguate_language(text, assumed_languages, db)
        if language is None:
            return None
    if 'pos' not in termdata:
        return standardized_concept_uri(language, text)
    else:
        pos = termdata['pos']
        if 'sense' not in termdata:
            return standardized_concept_uri(language, text, pos)
        else:
            etym = termdata.get('etym') or '1'
            sense_parts = ['wikt', etym, termdata['sense']]
            return standardized_concept_uri(language, text, pos, *sense_parts)


def disambiguate_language(text, assumed_languages, db):
    """
    Some Wiktionary links simply point to a term without specifying what
    language it's in. In that case, we have to guess.

    The possible languages are:

        - The language of the Wiktionary it's in
        - The language of the other term in the assertion

    We accept one of the possible languages if we have seen the term defined
    in that language in Wiktionary. Ideally, this leaves us with one
    possibility. But if we're left with 2 or 0, we default to the language
    of the other term.
    """
    if len(assumed_languages) == 1:
        return assumed_languages[0]

    ok_languages = []
    for language in assumed_languages:
        c = db.cursor()
        c.execute('SELECT * from titles where language=? and title=? limit 1',
                  (language, text))
        if c.fetchone():
            ok_languages.append(language)

    if len(ok_languages) == 0:
        return None
    else:
        return ok_languages[0]


def segmented_stream(input_file):
    """
    Read a JSON stream delimited by 'heading' entries, marking where the parser
    started parsing a new page. We distinguish these entries by the fact that
    they contain a 'title' key.

    Yield tuples of (heading, [items]), where [items] are the stream items
    that appear under the given heading.
    """
    heading = None
    items = []
    for item in read_json_stream(input_file):
        if 'title' in item:
            if heading is not None:
                yield heading, items
            heading = item
            items.clear()
        else:
            items.append(item)
    if heading is not None:
        yield heading, items


def read_wiktionary(input_file, db_file, output_file):
    db = sqlite3.connect(db_file)
    out = MsgpackStreamWriter(output_file)
    for heading, items in segmented_stream(input_file):
        language = heading['language']
        dataset = '/d/wiktionary/{}'.format(language)
        url_title = heading['title'].replace(' ', '_')
        web_source = '/s/web/{}.wiktionary.org/wiki/{}'.format(language, url_title)
        for item in items:
            tfrom = item['from']
            tto = item['to']
            assumed_languages = [language]
            lang1 = tfrom.get('language')
            lang2 = tto.get('language')
            if lang1 and (lang1 not in assumed_languages) and valid_language(lang1):
                assumed_languages.append(lang1)
            if lang2 and (lang2 not in assumed_languages) and valid_language(lang2):
                assumed_languages.append(lang2)

            cfrom = transform_term(tfrom, assumed_languages, db)
            cto = transform_term(tto, assumed_languages, db)
            if cfrom is None or cto is None:
                continue

            rel, switch = transform_relation(item['rel'])
            if rel is None:
                continue
            if switch:
                cfrom, cto = cto, cfrom

            sources = [web_source, PARSER_RULE]
            weight = 1.
            if rel == '/r/EtymologicallyDerivedFrom':
                weight = 0.5
            edge = make_edge(rel, cfrom, cto, dataset=dataset, weight=weight,
                             sources=sources,
                             surfaceStart=tfrom['text'], surfaceEnd=tto['text'],
                             license=Licenses.cc_sharealike)
            out.write(edge)
    out.close()

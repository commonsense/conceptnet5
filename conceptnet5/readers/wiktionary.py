from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.languages import ALL_LANGUAGES
from conceptnet5.edges import make_edge
from conceptnet5.uri import Licenses, uri_prefix
import sqlite3
import pathlib
import os
import re
from collections import Counter
import langcodes
from langcodes.tag_parser import LanguageTagError


PARSER_RULE = '/s/process/wikiparsec/1'


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
                    # For all non-definition relations, record the fact that
                    # the given entry name exists in the given language. We'll
                    # use these to disambiguate definitions later.
                    if item['rel'] != 'definition':
                        if 'language' in tfrom and valid_language(tfrom['language']):
                            add_title(db, file_language, tfrom['language'], tfrom['text'])
                        if 'language' in tto and valid_language(tto['language']):
                            add_title(db, file_language, tto['language'], tto['text'])

                    # Record word forms so we can build a lemmatizer from them.
                    if item['rel'].startswith('form/'):
                        form_name = item['rel'][5:]
                        # Look for the part of speech, first in the 'from' term,
                        # then in the 'to' term.
                        pos = tfrom.get('pos', tto.get('pos', '?'))

                        # Use only Etymology 1 entries for learning word forms.
                        if (tfrom.get('etym') or '1') == '1':
                            language = tfrom.get('language', tto.get('language'))
                            if language is not None and tfrom['text'] != tto['text']:
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
    if not code or code == 'und' or '-pro' in code:
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
        (file_language, language, title.lower())
    )


def add_form(db, file_language, language, word, pos, root, form):
    db.execute(
        "INSERT INTO forms (site_language, language, word, pos, root, form) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (file_language, language, word.lower(), pos.lower(), root.lower(), form.lower())
    )


WIKT_RELATIONS = {
    "link": ("/r/RelatedTo", False),
    "related": ("/r/RelatedTo", False),
    "synonym": ("/r/Synonym", False),
    "antonym": ("/r/Antonym", False),
    "distinct": ("/r/DistinctFrom", False),
    "hypernym": ("/r/IsA", False),
    "holonym": ("/r/PartOf", False),
    "troponym": ("/r/MannerOf", True),
    "context": ("/r/HasContext", False),
    "derived": ("/r/DerivedFrom", True),
    "derived/etym": ("/r/EtymologicallyDerivedFrom", True),
    "related/etym": ("/r/EtymologicallyRelatedTo", False),
    "form": ("/r/FormOf", False),
    "variant": ("/r/FormOf", True),
    "diminutive": ("/r/FormOf", True),
    "augmentative": ("/r/FormOf", True),
    "coordinate": ("/r/SimilarTo", False),
    "quasi-synonym": ("/r/SimilarTo", False),
    "translation": ("/r/Synonym", False),
    "definition": (None, False)
}


def transform_relation(rel):
    if rel.startswith('form/'):
        return "/r/FormOf", False
    else:
        return WIKT_RELATIONS[rel]


def transform_term(data_language, termdata, assumed_languages, db, use_etyms=True):
    text = termdata['text']
    language = termdata.get('language')
    if language is None:
        language = disambiguate_language(text, assumed_languages, db)
    if not valid_language(language):
        return None

    # Remove unnecessary subtags from the Wiktionary language
    if '-' in language and language not in ALL_LANGUAGES:
        language = language.split('-')[0]

    if 'pos' not in termdata:
        return standardized_concept_uri(language, text)
    else:
        pos = termdata['pos']
        etym_sense = None
        if use_etyms:
            etym_sense = etym_label(data_language, termdata)
        if etym_sense is not None:
            return standardized_concept_uri(language, text, pos, 'wikt', etym_sense)
        else:
            return standardized_concept_uri(language, text, pos)


def etym_label(language, term):
    if 'etym' not in term or not term['etym']:
        return None

    return "{}_{}".format(language, term['etym'])


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
    """
    Convert a stream of parsed Wiktionary data into ConceptNet edges.

    A `db_file` containing all known words in all languages must have already
    been prepared from the same data.
    """
    db = sqlite3.connect(db_file)
    out = MsgpackStreamWriter(output_file)
    for heading, items in segmented_stream(input_file):
        language = heading['language']
        title = heading['title']
        dataset = '/d/wiktionary/{}'.format(language)
        url_title = heading['title'].replace(' ', '_')
        web_url = 'http://{}.wiktionary.org/wiki/{}'.format(language, url_title)
        web_source = '/s/resource/wiktionary/{}'.format(language)

        source = {
            'contributor': web_source,
            'process': PARSER_RULE
        }

        # Scan through the 'from' items, such as the start nodes of
        # translations, looking for distinct etymologies. If we get more than
        # one etymology for a language, we need to distinguish them as
        # different senses in that language.
        all_etyms = {
            (item['from']['language'], etym_label(language, item['from']))
            for item in items
            if 'language' in item['from'] and item['from']['text'] == title
            and etym_label(language, item['from']) is not None
        }
        word_languages = {wlang for (wlang, _) in all_etyms}
        for wlang in sorted(word_languages):
            cpage = standardized_concept_uri(wlang, title)
            ld_edge = make_edge(
                '/r/ExternalURL', cpage, web_url,
                dataset=dataset, weight=0.25, sources=[source],
                license=Licenses.cc_sharealike
            )
            out.write(ld_edge)
        etym_to_translation_sense = {}
        language_etym_counts = Counter(lang for (lang, etym) in all_etyms)
        polysemous_languages = {
            lang for lang in language_etym_counts
            if language_etym_counts[lang] > 1
        }

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

            cfrom = transform_term(
                language, tfrom, assumed_languages, db,
                use_etyms=(lang1 in polysemous_languages)
            )
            cpage = cfrom
            cto = transform_term(
                language, tto, assumed_languages, db,
                use_etyms=(lang2 in polysemous_languages)
            )

            if cfrom is None or cto is None:
                continue
            if uri_prefix(cfrom, 3) == uri_prefix(cto, 3):
                continue

            rel, switch = transform_relation(item['rel'])
            if rel is None:
                continue
            if switch:
                cfrom, cto = cto, cfrom

            # When translations are separated by sense, use only the first
            # sense we see for each etymology. That will have the most
            # representative translations.
            if item['rel'] == 'translation':
                etym_key = (tfrom['language'], etym_label(language, tfrom))
                sense = tfrom.get('sense', '')
                if etym_key in etym_to_translation_sense:
                    if etym_to_translation_sense[etym_key] != sense:
                        continue
                else:
                    etym_to_translation_sense[etym_key] = sense

            weight = 1.
            if rel == '/r/EtymologicallyRelatedTo':
                weight = 0.25
            edge = make_edge(rel, cfrom, cto, dataset=dataset, weight=weight,
                             sources=[source],
                             surfaceStart=tfrom['text'],
                             surfaceEnd=tto['text'],
                             license=Licenses.cc_sharealike)
            out.write(edge)

    out.close()

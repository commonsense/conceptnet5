import sqlite3
import wordfreq
from conceptnet5.util import get_data_filename

WORDFREQ_LANGUAGES = set(wordfreq.available_languages())
WORDFREQ_LANGUAGES_LARGE = set(wordfreq.available_languages('large'))


class DBLemmatizer:
    def __init__(self):
        self.db = sqlite3.connect(get_data_filename('db/wiktionary.db'))

    def lookup(self, language, word, pos=None):
        cursor = self.db.cursor()
        if pos:
            cursor.execute(
                "SELECT site_language, root, form FROM forms "
                "WHERE language=? AND word=? AND pos=? "
                "AND root like '__%'",
                (language, word, pos)
            )
        else:
            cursor.execute(
                "SELECT site_language, root, form FROM forms "
                "WHERE language=? AND word=? "
                "AND root like '__%'",
                (language, word)
            )
        rows = list(cursor.fetchall())
        if len(rows) == 0:
            return (word, '')
        elif len(rows) == 1:
            _site_lang, root, form = rows[0]
            return root, form
        else:
            possibilities = []
            for row in rows:
                site_lang, root, form = row
                if site_lang == 'en':
                    goodness = 1.
                else:
                    goodness = 0.
                if language in WORDFREQ_LANGUAGES_LARGE:
                    goodness += wordfreq.word_frequency(root, language, 'large')
                elif language in WORDFREQ_LANGUAGES:
                    goodness += wordfreq.word_frequency(root, language)
                possibilities.append((-goodness, site_lang, root, form))
            possibilities.sort()
            _, site_lang, root, form = possibilities[0]

            # We don't have consistent labels yet for forms labeled in
            # non-English Wiktionaries
            if site_lang != 'en':
                form = '?'
            if root == word:
                form = ''
            return root, form

LEMMATIZER = DBLemmatizer()


def lemmatize(language, word, pos=None):
    """
    Run a dictionary-based lemmatizer (fancy stemmer) on a word. Return the root
    word and the word form that was found. The word form will be the empty
    string if the word was unchanged.

    >>> lemmatize('eating')
    ('eat', 'pres+ptcp')
    >>> lemmatize('carrots')
    ('carrot', 'p')
    >>> lemmatize('is')
    ('be', '3+s+pres')
    >>> lemmatize('good')
    ('good', '')

    >>> lem.lookup('es', 'tengo', 'v')
    ('tener', '1+s+pres+ind')
    """
    return LEMMATIZER.lookup(language, word, pos)

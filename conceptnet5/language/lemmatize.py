import sqlite3
import wordfreq
from conceptnet5.util import get_data_filename
from conceptnet5.uri import split_uri, join_uri


WORDFREQ_LANGUAGES = set(wordfreq.available_languages())
WORDFREQ_LANGUAGES_LARGE = set(wordfreq.available_languages('large'))

# These are the languages for which we are reasonably confident in Wiktionary's
# lemmatization.
LEMMATIZED_LANGUAGES = {
    # Languages supported by wordfreq:
    'ar', 'de', 'el', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'pt', 'ru',
    'sv', 'tr',

    # Other languages:
    'ast', 'gl', 'ca', 'oc', 'nrf',
    'no', 'da', 'af',
    'ga', 'gd', 'is', 'fo', 'gv', 'cy',
    'hsb', 'cs', 'sh', 'sk', 'sl', 'lv',
    'fi', 'hu', 'ro', 'bg',
    'hy', 'ka', 'rup', 'uk',
    'la', 'ang', 'grc', 'xcl', 'fro', 'non',
    'eo', 'io', 'vo',

    # Languages left out:
    #   - No lemmatizer needed: zh, ms
    #   - Not enough information in:
    #     ja, se, fa, sq, mg, he, mk, sa, nv, hi, fil, eu
    #   - Script problems: sh
    #   - Parsing problems: et
    #   - Tokenization problems: th

}


# Include some exceptions to lemmatization where we don't want to just rely
# on what Wiktionary says.
EXCEPTIONS = {
    'en': {
        # Wiktionary's entry on the plural sense of 'people' is special
        'people': ('person', 'p'),

        # 'bathing' should not stem to 'bath'
        'bathing': ('bathe', 'pres+ptcp'),

        # Wiktionary adds a period to the end of the stem 'here is'
        "here's": ('here is', 'contraction'),

        # 'gentlemen' should be the plural of 'gentleman', not of 'sir'
        "gentlemen": ('gentleman', 'p'),

        # Instead of using the past-tense template, someone just typed its
        # output into the entry for 'improvised', so we can't recognize it
        'improvised': ('improvise', 'past'),

        # Not 'secret'
        'secreted': ('secrete', 'past'),

        # The informal usage 'you is' ended up overriding the normal usage
        'is': ('be', '3+s+pres'),

        # Convert Penn Treebank word fragments into appropriate words
        "n't": ('not', 'treebank+contraction'),
        'wo': ('will', 'treebank+contraction'),
        'ca': ('can', 'treebank+contraction'),

        # German is confused about English words for size
        'big': ('big', ''),
        'bigger': ('big', 'comp'),
        'biggest': ('big', 'sup'),
        'smaller': ('small', 'comp'),
        'smallest': ('small', 'sup'),
    },

    # Fix some random template errors in other languages
    'it': {
        'reclamo': ('reclamare', '1+s+pres'),
    },
    'fr': {
        'flames': ('flamer', '2+s+pres+indc'),
    },
    'pt': {
        'voleibolistas': ('voleibolista', 'p'),
        'bilabiais': ('bilabial', 'p')
    },
    'es': {
        'voleibolistas': ('voleibolista', 'p'),
    }
}

EXCEPTIONS_FIXED = {
    # These words could obscurely be interpreted as forms of other words,
    # but let's not let that happen. Instead, these words will be forced to
    # lemmatize to themselves.
    'en': {
        'agenda', 'alba', 'archer', 'art', 'ascii', 'bad', 'bare', 'bee',
        'belated', 'bin', 'bio', 'bonkers', 'book', 'brake', 'bummer', 'camper',
        'carmen', 'ceiling', 'cola', 'conceited', 'crew', 'crown', 'di',
        'dive', 'drug', 'dui', 'during', 'feed', 'fleming', 'fore', 'greece',
        'hades', 'hinder', 'hole', 'holmes', 'jus', 'kent', 'ky', 'liver', 'low',
        'ment', 'mini', 'molasses', 'mos', 'naked', 'number', 'physics', 'plaid', 'prove',
        'raft', 'rebound', 'red', 'reed', 'rid', 'rift', 'rowling', 'rugged',
        'sacred', 'seed', 'sept', 'sheep', 'shore', 'sideways', 'slang', 'sod',
        'span', 'spice', 'sticker', 'stove', 'vegas', 'wan', 'weed', 'wilt', 'writ',

        # These have to be included because of German
        'the', 'most', 'put', 'gun'
    },
    'de': {
        'die', 'der', 'das', 'ein', 'mir', 'uns', 'klein'
    }
}


QUERY = """
SELECT root, form, pos FROM forms
WHERE language=? AND word=?
AND root LIKE '__%' AND form != 'alternate'
AND form NOT LIKE '%short%' AND form NOT LIKE '%Short%'
AND NOT (site_language='de' AND
  (form='masculine' OR form='feminine' OR form='diminutive'))
"""


LEMMA_FILENAME = get_data_filename('db/wiktionary.db')


class DBLemmatizer:
    def __init__(self, filename=LEMMA_FILENAME):
        self.filename = filename
        self.db = None

    def lookup(self, language, word, pos=None):
        if self.db is None:
            self.db = sqlite3.connect(self.filename)
        if language not in LEMMATIZED_LANGUAGES:
            return word, ''
        exceptions = EXCEPTIONS.get(language, {})
        if word in exceptions:
            return exceptions[word]
        exceptions_fixed = EXCEPTIONS_FIXED.get(language, set())
        if word in exceptions_fixed:
            return word, ''

        cursor = self.db.cursor()
        if pos:
            cursor.execute(QUERY + ' AND pos=?', (language, word, pos))
        else:
            cursor.execute(QUERY, (language, word))

        rows = list(cursor.fetchall())
        if len(rows) == 0:
            return word, ''
        elif len(rows) == 1:
            root, form, pos = rows[0]
            return root, form
        else:
            possibilities = []
            for row in rows:
                root, form, pos = row
                if language in WORDFREQ_LANGUAGES_LARGE:
                    goodness = wordfreq.word_frequency(root, language, 'large')
                elif language in WORDFREQ_LANGUAGES:
                    goodness = wordfreq.word_frequency(root, language)
                else:
                    goodness = 0.
                if pos == 'n':
                    goodness += 1.
                if form == 'positiv' or form == 'singular' and root != word:
                    goodness -= 2.
                if goodness >= 0:
                    possibilities.append((-goodness, root, form))
            possibilities.sort()
            if not possibilities:
                return word, ''
            _, root, form = possibilities[0]

            if root == word:
                form = ''
            return root, form

    def lemmatize_uri(self, uri):
        pieces = split_uri(uri)
        if len(pieces) < 2:
            return uri
        language = pieces[1]
        text = pieces[2]
        rest = pieces[3:]
        if rest:
            pos = rest[0]
        else:
            pos = None

        root, _form = self.lookup(language, text, pos)
        return join_uri('c', language, root, *rest)

LEMMATIZER = DBLemmatizer()


def lemmatize(language, word, pos=None):
    """
    Run a dictionary-based lemmatizer (fancy stemmer) on a word. Return the root
    word and the word form that was found. The word form will be the empty
    string if the word was unchanged.

    >>> lemmatize('en', 'eating')
    ('eat', 'pres+ptcp')
    >>> lemmatize('en', 'carrots')
    ('carrot', 'p')
    >>> lemmatize('en', 'is')
    ('be', '3+s+pres')
    >>> lemmatize('en', 'good')
    ('good', '')
    >>> lemmatize('es', 'tengo', 'v')
    ('tener', '1+s+pres+ind')
    """
    return LEMMATIZER.lookup(language, word, pos)


def lemmatize_uri(uri):
    return LEMMATIZER.lemmatize_uri(uri)

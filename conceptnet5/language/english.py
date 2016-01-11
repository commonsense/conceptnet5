# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

"""
Tools for working with English text and reducing it to a normal form.

In English, we remove a very small number of stopwords, and then apply a
modified version of Morphy, the stemmer (lemmatizer) used in WordNet.  The
modifications mostly involve heuristics for when to apply noun or verb
transformations to words whose part of speech is ambiguous.
"""
from ..util import get_support_data_filename
from .token_utils import simple_tokenize
import re
morphy = None

STOPWORDS = ['the', 'a', 'an']

EXCEPTIONS = {
    # Avoid obsolete and obscure roots, the way lexicographers don't.
    'wrought': 'wrought',   # not 'work'
    'media': 'media',       # not 'medium'
    'installed': 'install', # not 'instal'
    'installing': 'install',# not 'instal'
    'synapses': 'synapse',  # not 'synapsis'
    'soles': 'sole',        # not 'sol'
    'pubes': 'pube',        # not 'pubis'
    'dui': 'dui',           # not 'duo'
    'taxis': 'taxi',        # not 'taxis'

    # Work around errors that Morphy makes.
    'alas': 'alas',
    'corps': 'corps',
    'cos': 'cos',
    'enured': 'enure',
    'fiver': 'fiver',
    'hinder': 'hinder',
    'lobed': 'lobe',
    'offerer': 'offerer',
    'outer': 'outer',
    'sang': 'sing',
    'singing': 'sing',
    'solderer': 'solderer',
    'tined': 'tine',
    'twiner': 'twiner',
    'us': 'us',

    # Stem common nouns whose plurals are apparently ambiguous
    'teeth': 'tooth',
    'things': 'thing',
    'people': 'person',

    # Tokenization artifacts
    'wo': 'will',
    'ca': 'can',
    "n't": 'not',
}

AMBIGUOUS_EXCEPTIONS = {
    # Avoid nouns that shadow more common verbs.
    'am': 'be',
    'as': 'as',
    'are': 'be',
    'ate': 'eat',
    'bent': 'bend',
    'drove': 'drive',
    'fell': 'fall',
    'felt': 'feel',
    'found': 'find',
    'has': 'have',
    'lit': 'light',
    'lost': 'lose',
    'sat': 'sit',
    'saw': 'see',
    'sent': 'send',
    'shook': 'shake',
    'shot': 'shoot',
    'slain': 'slay',
    'spoke': 'speak',
    'stole': 'steal',
    'sung': 'sing',
    'thought': 'think',
    'tore': 'tear',
    'was': 'be',
    'won': 'win',
    'feed': 'feed',
}


def _word_badness(word):
    """
    Assign a heuristic to possible outputs from Morphy. Minimizing this
    heuristic avoids incorrect stems.
    """
    if word.endswith('e'):
        return len(word) - 2
    elif word.endswith('ess'):
        return len(word) - 10
    elif word.endswith('ss'):
        return len(word) - 4
    else:
        return len(word)


def _morphy_best(word, pos=None):
    """
    Get the most likely stem for a word using Morphy, once the input has been
    pre-processed by morphy_stem().
    """

    global morphy
    if morphy is None:
        from nltk.corpus import wordnet
        morphy = wordnet._morphy


    results = []
    if pos is None:
        pos = 'nvar'
    for pos_item in pos:
        results.extend(morphy(word, pos_item))
    if not results:
        return None
    results.sort(key=lambda x: _word_badness(x))
    return results[0]


def morphy_stem(word, pos=None):
    """
    Get the most likely stem for a word. If a part of speech is supplied,
    the stem will be more accurate.

    Valid parts of speech are:

    - 'n' or 'NN' for nouns
    - 'v' or 'VB' for verbs
    - 'a' or 'JJ' for adjectives
    - 'r' or 'RB' for adverbs

    Any other part of speech will be treated as unknown.
    """
    # FIXME: strip punctuation that may still be attached to the word
    word = word.lower()
    if pos is not None:
        if pos.startswith('NN'):
            pos = 'n'
        elif pos.startswith('VB'):
            pos = 'v'
        elif pos.startswith('JJ'):
            pos = 'a'
        elif pos.startswith('RB'):
            pos = 'r'
    if pos is None and word.endswith('ing') or word.endswith('ed'):
        pos = 'v'
    if pos is not None and pos not in 'nvar':
        pos = None
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if pos is None:
        if word in AMBIGUOUS_EXCEPTIONS:
            return AMBIGUOUS_EXCEPTIONS[word]
    return _morphy_best(word, pos) or word


def english_filter(tokens):
    """
    Given a list of tokens, remove a small list of English stopwords, and
    reduce the words to their WordNet roots using Morphy.
    """
    non_stopwords = [morphy_stem(token) for token in tokens if token not in STOPWORDS]
    if non_stopwords and non_stopwords[0] == 'to':
        non_stopwords = non_stopwords[1:]
    if non_stopwords:
        return non_stopwords
    else:
        return tokens


class SimpleLemmatizer:
    def __init__(self, language):
        self.language = language
        self.mapping = {}
        self.patterns = []
        self._load()

    def _load(self):
        from nltk.corpus import wordnet
        self.wordnet = wordnet

        self.mapping.clear()
        self.patterns.clear()
        self._load_patterns()
        self._load_exceptions()
        self._load_unchanged()

    def _load_patterns(self):
        filename = get_support_data_filename('morphology/{0}_patterns.txt'.format(self.language))
        for line in open(filename, encoding='utf-8'):
            pattern, replacement, pos, morph = line.rstrip().split(None, 3)
            if morph == '-':
                morph = ''
            re_pattern = re.compile(pattern.replace('*', '(.+)') + '$')
            replacement = replacement.replace('*', r'\1')
            self.patterns.append((re_pattern, replacement, pos.lower(), morph))

    def _load_exceptions(self):
        for pos in ['noun', 'verb', 'adj']:
            filename = get_support_data_filename('morphology/{0}_{1}.txt'.format(self.language, pos))
            for line in open(filename, encoding='utf-8'):
                before, after, morph = line.rstrip().split(None, 2)
                self.mapping[before] = (after, morph)

    def _load_unchanged(self):
        filename = get_support_data_filename('morphology/{0}_unchanged.txt'.format(self.language))
        for line in open(filename, encoding='utf-8'):
            word = line.rstrip()
            self.mapping[word] = (word, '')

    def lookup(self, word):
        if word in self.mapping:
            return self.mapping[word]

        if len(word) > 3:
            for re_pattern, replacement, pos, morph in self.patterns:
                match = re_pattern.match(word)
                if match:
                    replaced = re_pattern.sub(replacement, word)
                    if self.wordnet.lemmas(replaced, pos):
                        self.mapping[word] = (replaced, morph)
                        return (replaced, morph)

        self.mapping[word] = (word, '')
        return (word, '')

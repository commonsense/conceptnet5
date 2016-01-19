# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

"""
Tools for working with English text and reducing it to a normal form.

In English, we remove a very small number of stopwords, and then apply a
modified version of Morphy, the stemmer (lemmatizer) used in WordNet.
"""
from ..util import get_support_data_filename
from .token_utils import simple_tokenize
from collections import defaultdict
import re

STOPWORDS = ['the', 'a', 'an']


def english_filter(tokens):
    """
    Given a list of tokens, remove a small list of English stopwords, and
    reduce the words to their WordNet roots using a simple lemmatizer.
    """
    non_stopwords = [lemmatize(token) for token in tokens if token not in STOPWORDS]
    if non_stopwords and non_stopwords[0] == 'to':
        non_stopwords = non_stopwords[1:]
    if non_stopwords:
        return non_stopwords
    else:
        return tokens


class SimpleLemmatizer:
    def __init__(self, language):
        self.language = language
        self._mapping = {}
        self._vocab = defaultdict(set)
        self._patterns = []
        self.loaded = False

    def _load(self):
        self._mapping.clear()
        self._patterns.clear()
        self._vocab.clear()
        self._load_patterns()
        self._load_exceptions()
        self._load_unchanged()
        self._load_vocab()
        self.loaded = True

    def _load_vocab(self):
        filename = get_support_data_filename('morphology/{0}_vocab.txt'.format(self.language))
        for line in open(filename, encoding='utf-8'):
            word, pos = line.rstrip().split('\t', 1)
            self._vocab[pos].add(word)

    def _load_patterns(self):
        filename = get_support_data_filename('morphology/{0}_patterns.txt'.format(self.language))
        for line in open(filename, encoding='utf-8'):
            pattern, replacement, pos, morph = line.rstrip().split(None, 3)
            if morph == '-':
                morph = ''
            re_pattern = re.compile(pattern.replace('*', '(.+)') + '$')
            replacement = replacement.replace('*', r'\1')
            self._patterns.append((re_pattern, replacement, pos.lower(), morph))

    def _load_exceptions(self):
        for pos in ['noun', 'verb', 'adj']:
            filename = get_support_data_filename('morphology/{0}_{1}.txt'.format(self.language, pos))
            for line in open(filename, encoding='utf-8'):
                before, after, morph = line.rstrip().split(None, 2)
                self._mapping[before] = (after, morph)

    def _load_unchanged(self):
        filename = get_support_data_filename('morphology/{0}_unchanged.txt'.format(self.language))
        for line in open(filename, encoding='utf-8'):
            word = line.rstrip()
            self._mapping[word] = (word, '')

    def lookup(self, word):
        if not self.loaded:
            self._load()

        word = word.lower()
        if word in self._mapping:
            return self._mapping[word]

        if len(word) > 3:
            for re_pattern, replacement, pos, morph in self._patterns:
                match = re_pattern.match(word)
                if match:
                    replaced = re_pattern.sub(replacement, word)
                    if replaced == word or replaced.lower() in self._vocab[pos.lower()]:
                        self._mapping[word] = (replaced, morph)
                        return (replaced, morph)

        self._mapping[word] = (word, '')
        return (word, '')


LEMMATIZER = SimpleLemmatizer('en')


def lemmatize(word):
    """
    Run a simple English lemmatizer (fancy stemmer) on a word. Return the root
    word and the ending (described very coarsely) that was removed.

    The root word will either be a WordNet lemma or the original word.

    >>> lemmatize('eating')
    ('eat', '+ing')
    >>> lemmatize('carrots')
    ('carrot', '+s')
    >>> lemmatize('is')
    ('be', '+s')
    >>> lemmatize('good')
    ('good', '')
    """
    stem, ending = LEMMATIZER.lookup(word)
    return stem


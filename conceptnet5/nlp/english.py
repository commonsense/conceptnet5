# -*- coding: utf-8 -*-
import nltk
from nltk.corpus import wordnet
import simplenlp
import re
EN = simplenlp.get('en')

try:
    morphy = wordnet.morphy
except LookupError:
    nltk.download('wordnet')
    morphy = wordnet.morphy

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
    'comics': 'comic',      # WordNet's root for this will make you nerd-rage
    'taxis': 'taxi',        # not 'taxis'

    # Stem common nouns whose plurals are apparently ambiguous
    'teeth': 'tooth',
    'things': 'thing',
    'people': 'person',
}

AMBIGUOUS_EXCEPTIONS = {
    # Avoid nouns that shadow more common verbs.
    'am': 'be',
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
    'stole': 'steal',
    'sung': 'sing',
    'thought': 'think',
    'tore': 'tear',
    'was': 'be',
    'won': 'win',
}

def morphy_stem(word, pos=None):
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
    if pos is None and word in AMBIGUOUS_EXCEPTIONS:
        return AMBIGUOUS_EXCEPTIONS[word]
    return (pos and morphy(word, pos)) or morphy(word) or word

def simple_stem(word):
    return EN.normalize(word).strip()

def tag_and_stem(text):
    tokens = tokenize(text)
    tagged = nltk.pos_tag(tokens)
    out = []
    for token, tag in tagged:
        if token.startswith('#'):
            out.append((token, 'TAG'))
        else:
            stem = morphy_stem(token, tag)
            out.append((stem, tag))
    return out

def un_camel_case(text):
    u"""
    Splits apart words that are written in CamelCase.

    Examples:

    >>> un_camel_case('1984ZXSpectrumGames')
        '1984 ZX Spectrum Games'

    >>> un_camel_case('aaAa aaAaA 0aA AAAa!AAA')
        'aa Aa aa Aa A 0 a A AA Aa! AAA'

    >>> un_camel_case(u'MotörHead')
        u'Mot\xf6r Head'

    This should not significantly affect text that is not camel-cased:
    >>> un_camel_case('ACM_Computing_Classification_System')
        'ACM Computing Classification System'
    
    >>> un_camel_case(u'Anne_Blunt,_15th_Baroness_Wentworth')
        u'Anne Blunt, 15 th Baroness Wentworth'

    >>> un_camel_case(u'Hindi-Urdu')
        u'Hindi-Urdu'
    """
    revtext = text[::-1]
    pieces = []
    while revtext:
        match = re.match(ur'^([A-Z]+|[^A-Z0-9 _]+[A-Z _]|[0-9]+|[ _]+|[^A-Z0-9]*[^A-Z0-9_ ]+)(.*)$', revtext)
        if match:
            pieces.append(match.group(1))
            revtext = match.group(2)
        else:
            print revtext
            pieces.append(revtext)
            revtext = ''
    revstr = ' '.join(piece.strip(' _') for piece in pieces if piece.strip(' _'))
    return revstr[::-1].replace('- ', '-')

def tokenize(text):
    return EN.tokenize(text.strip()).split()

def untokenize(tokens):
    if isinstance(tokens, basestring):
        text = tokens
    else:
        text = ' '.join(tokens)
    return EN.untokenize(text)

def good_lemma(lemma):
    return lemma and lemma not in STOPWORDS and lemma[0].isalnum()

def normalize(text):
    pieces = [morphy_stem(word) for word in tokenize(text)]
    pieces = [piece for piece in pieces if good_lemma(piece)]
    if not pieces:
        return text
    if pieces[0] == 'to':
        pieces = pieces[1:]
    return untokenize(pieces)

def normalize_topic(topic):
    # find titles of the form Foo (bar)
    topic = topic.replace('_', ' ')
    match = re.match(r'([^(]+) \(([^)]+)\)', topic)
    if not match:
        return normalize(topic), None
    else:
        return normalize(match.group(1)), 'n/'+match.group(2).strip(' _')

def normalize_english_assertion(graph, assertion):
    """
    Run the arguments (and possibly the relation) of `assertion` through
    the English text normalizer. Return a new assertion that uses the
    normalized forms, and add `normalized` links between them where
    appropriate.
    """
    relargs = graph.get_rel_and_args(assertion)
    rel = relargs[0]
    args = relargs[1:]
    if rel['type'] == 'concept':
        rel = graph.get_or_create_concept('en', normalize(rel['name']))
    concept_names = [normalize(arg['name']) for arg in args]

    concepts = [graph.get_or_create_concept('en', name)
                for name in concept_names]
    result = get_or_create_assertion(rel, concepts,
        {normalized: True}
    )
    graph.derive_normalized(assertion, result)
    return result

if __name__ == '__main__':
    print normalize("this is a test")


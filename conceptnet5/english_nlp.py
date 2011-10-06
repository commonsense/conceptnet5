import nltk
from nltk.corpus import wordnet
import simplenlp
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
    'teeth': 'tooth',       # not 'teeth'

    # Avoid nouns that shadow more common verbs.
    'was': 'be',
    'has': 'have',
    'won': 'win',
    'tore': 'tear',
    'sung': 'sing',
    'slain': 'slay',
    'shook': 'shake',
    'shot': 'shoot',
    'thought': 'think',
    'stole': 'steal',
    'sat': 'sit',
    'saw': 'see',
    'sent': 'send',
    'lost': 'lose',
    'lit': 'light',
    'found': 'find',
    'felt': 'feel',
    'fell': 'fall',
    'drove': 'drive',
    'am': 'be',
    'are': 'be',
    'ate': 'eat',
    'bent': 'bend',
}

def morphy_stem(word):
    word = word.lower()
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    elif word.endswith('ing') or word.endswith('ed'):
        return morphy(word, 'v') or morphy(word) or word
    else:
        # trust in wordnet
        return morphy(word) or word

def simple_stem(word):
    return EN.normalize(word).strip()

def tokenize(text):
    return EN.tokenize(text.strip()).split()

def untokenize(tokens):
    if isinstance(tokens, basestring):
        text = tokens
    else:
        text = ' '.join(tokens)
    return EN.untokenize(text)

def normalize(text):
    pieces = [morphy_stem(word) for word in tokenize(text)
              if word not in STOPWORDS]
    pieces = [piece for piece in pieces if piece]
    if not pieces:
        return text
    return untokenize(pieces)

def normalize_english_assertion(graph, assertion):
    """
    Run the arguments (and possibly the relation) of `assertion` through
    the English text normalizer. Return a new assertion that uses the
    normalized forms, and add `normalized` links between them where
    appropriate.
    """
    args = graph.get_args(assertion)
    rel = assertion['relation']
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

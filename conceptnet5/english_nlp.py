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

# Avoid obsolete roots, the way lexicographers don't
EXCEPTIONS = {
    'born': 'born',         # not 'bear'
    'wrought': 'wrought',   # not 'work'
    'media': 'media',       # not 'medium'
}

def morphy_stem(word):
    word = word.lower()
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    return morphy(word, 'v') or morphy(word, 'n') or word

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
    return ' '.join(pieces)

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

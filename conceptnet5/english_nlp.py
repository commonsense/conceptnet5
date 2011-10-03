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

def morphy_stem(word):
    word = word.lower()
    return morphy(word, 'v') or morphy(word, 'n') or word

def simple_stem(word):
    return EN.normalize(word).strip()

def tokenize(text):
    return EN.tokenize(text.strip()).split()

def normalize(text):
    pieces = [morphy_stem(word) for word in tokenize(text)
              if word not in STOPWORDS]
    pieces = [piece for piece in pieces if piece]
    return ' '.join(pieces)

def normalize_english_assertion(graph, assertion):
    args = graph.get_args(assertion)
    concept_names = [normalize(arg['name']) for arg in args]

    concepts = [graph.get_or_create_concept('en', name)
                for name in concept_names]

if __name__ == '__main__':
    print normalize("this is a test")

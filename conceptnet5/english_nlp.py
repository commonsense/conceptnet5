#from nltk.corpus import wordnet
import simplenlp
EN = simplenlp.get('en')

STOPWORDS = ['the', 'a', 'an']

def morphy_stem(word):
    from nltk.corpus import wordnet
    morphy = wordnet.morphy
    word = word.lower()
    return morphy(word, 'v') or morphy(word, 'n') or word

def simple_stem(word):
    return EN.normalize(word)

def tokenize(text):
    return EN.tokenize(text.strip()).split()

def normalize(text):
    pieces = [simple_stem(word) for word in tokenize(text) if word not in STOPWORDS]
    return ' '.join(pieces)

if __name__ == '__main__':
    print normalize("this is a test")

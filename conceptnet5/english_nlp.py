from nltk.corpus import wordnet
import simplenlp
EN = simplenlp.get('en')

STOPWORDS = ['the', 'a', 'an']

def morphy_stem(word):
    word = word.lower()
    return wordnet.morphy(word, 'v') or wordnet.morphy(word, 'n') or word

def tokenize(text):
    return EN.tokenize(text.strip()).split()

def normalize(text):
    pieces = [morphy_stem(word) for word in tokenize(text) if word not in STOPWORDS]
    return ' '.join(pieces)

if __name__ == '__main__':
    print normalize("this is a test")

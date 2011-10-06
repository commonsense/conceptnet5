import simplenlp
EN = simplenlp.get('en')
from conceptnet5.english_nlp import normalize

def check_line(line):
    parts = line.strip().split()
    norm = normalize(parts[0])
    if norm != parts[1]:
        print "Original: %s / WordNet: %s / conceptnet: %s" %\
            (parts[0], parts[1], norm)

def compare_words():
    for line in open('/Users/rspeer/nltk_data/corpora/wordnet/noun.exc'):
        check_line(line)

    for line in open('/Users/rspeer/nltk_data/corpora/wordnet/verb.exc'):
        check_line(line)

if __name__ == '__main__':
    compare_words()


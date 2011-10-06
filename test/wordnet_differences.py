import simplenlp
EN = simplenlp.get('en')

def check_line(line):
    parts = line.strip().split()
    norm = EN.normalize(parts[0])
    if norm != parts[1]:
        print "Original: %s / WordNet: %s / simplenlp: %s" %\
            (parts[0], parts[1], norm)

def compare_words():
    for line in open('/Users/rspeer/nltk_data/corpora/wordnet/noun.exc'):
        check_line(line)

    for line in open('/Users/rspeer/nltk_data/corpora/wordnet/verb.exc'):
        check_line(line)


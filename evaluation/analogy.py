from wordsim import text_to_vector, cos_diff
from conceptnet5.nodes import normalized_concept_uri
from conceptnet5.util import get_support_data_filename
from sklearn.preprocessing import normalize

def read_symrel():
    """
    Parses the SYM-REL database from Mikolov et al.
    """
    filename = get_support_data_filename('rel/questions-words.txt')
    with open(filename) as file:
        for line in file:
            if line.startswith(': gram'):
                break
            if line.startswith(':'):
                continue
            yield line.split()

def evaluate(standard, assoc, verbose=True):
    correct = 0
    total = 0
    for a,b,c,d in standard:
        if total % 10 == 0:
            print(correct, total)
        av = text_to_vector(a, assoc)
        bv = text_to_vector(b, assoc)
        cv = text_to_vector(c, assoc)
        terms = assoc.terms_similar_to_vector(normalize(bv-av+cv)[0])
        d2 = terms[0]
        print(a,b,c,d,terms[:2])
        if d2[0] ==  normalized_concept_uri('en', d):
            correct += 1
        total += 1

    if verbose:
        print(100*correct/total)

    return (correct, total)

def test(assoc):
    print("SYM-REL")
    evaluate(read_symrel(), assoc)

def main(dir):
    assoc = AssocSpace.load_dir(dir)
    test(assoc)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])

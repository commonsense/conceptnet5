from assoc_space import AssocSpace, SparseEntryStorage
from collections import defaultdict
import codecs
import argparse


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return ':' in uri or uri.count('_') >= 3


def concept_is_frequent_enough(uri, counts):
    """
    Require that concepts in English appear at least three times, and
    in other languages, at least twice. Being the negation of a concept
    counts as one appearance, implicitly.
    """
    score = counts.get(uri, 0) + uri.endswith('/neg') - ('/en/' in uri)
    return score >= 2


def negate_concept(concept):
    """
    The representation of a negative association, here, is that one end
    involves a concept with `/neg` appended to its URI. Negating a concept
    means either adding or removing the `/neg`.
    """
    if concept.endswith('/neg'):
        return concept[:-4]
    else:
        return concept + '/neg'


def build_assoc_space(input_file, output_dir):
    print('loading')
    counts = defaultdict(int)
    triples = []

    for line in codecs.open(input_file, encoding='utf-8'):
        left, right, value = line.strip().split('\t')[:3]
        if not concept_is_bad(left) and not concept_is_bad(right):
            value = float(value)
            triples.append((value, left, right))
            counts[left] += 1
            counts[right] += 1

    print('filtering entries')
    sparse = SparseEntryStorage()
    for (value, left, right) in triples:
        if concept_is_frequent_enough(left, counts) and concept_is_frequent_enough(right, counts) and left != right:
            sparse.add_entry((value, left, right))
    del triples

    # Add links from a concept to itself, and negative links to its opposite if it's there
    for concept in counts:
        if concept_is_frequent_enough(concept, counts):
            sparse.add_entry((1., concept, concept))
            negation = negate_concept(concept)
            if concept_is_frequent_enough(negation, counts):
                sparse.add_entry((-1., concept, negation))

    print('making assoc space')
    space = AssocSpace.from_sparse_storage(sparse, k=300, offset_weight=1e-4)

    print('saving')
    space.save_dir(output_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_dir')

    args = parser.parse_args()
    build_assoc_space(args.input_file, args.output_dir)

from collections import defaultdict
import argparse
from conceptnet5.uri import split_uri, join_uri
from conceptnet5.nodes import is_negative_relation


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return ':' in uri or uri.count('_') >= 3 or uri.startswith('/a/')


def generalized_uri(uri):
    pieces = split_uri(uri)
    return join_uri(*pieces[:3])


def reduce_assoc(filename, output_filename, cutoff=3, en_cutoff=3, verbose=True):
    """
    Removes uncommon associations and associations unlikely to be useful.
    This function expects files of the form part_*.csv in `dirname` and will
    create `reduced.csv` in `dirname`.

    All concepts that occur fewer than `cutoff` times will be removed.
    All English concepts that occur fewer than `en_cutoff` times will be removed.
    """
    counts = defaultdict(int)
    senses = {}
    with open(filename, encoding='utf-8') as file:
        for line in file:
            left, right, _value, _dataset, rel = line.rstrip().split('\t')
            if rel == '/r/SenseOf':
                if right in senses:
                    senses[right] = '*'
                else:
                    senses[right] = left
            else:
                gleft = generalized_uri(left)
                gright = generalized_uri(right)
                counts[gleft] += 1
                counts[gright] += 1

    filtered_concepts = {
        concept for (concept, count) in counts.items()
        if (
            count >= en_cutoff or
            (not concept.startswith('/c/en/') and count >= cutoff)
        )
    }

    with open(output_filename, 'w', encoding='utf-8') as out:
        with open(filename, encoding='utf-8') as file:
            for line in file:
                left, right, value, dataset, rel = line.rstrip().split('\t', 4)
                if concept_is_bad(left) or concept_is_bad(right) or is_negative_relation(rel):
                    continue
                fvalue = float(value)
                gleft = generalized_uri(left)
                gright = generalized_uri(right)
                if (
                    gleft in filtered_concepts and
                    gright in filtered_concepts and
                    fvalue != 0
                ):
                    if rel != '/r/SenseOf' and left in senses and senses[left] != '*':
                        sleft = senses[left]
                    else:
                        sleft = left
                    if rel != '/r/SenseOf' and right in senses and senses[right] != '*':
                        sright = senses[right]
                    else:
                        sright = right
                    if sleft != sright:
                        line = '\t'.join([sleft, sright, value, dataset, rel])
                        print(line, file=out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename')
    parser.add_argument('output_filename')

    args = parser.parse_args()
    reduce_assoc(args.input_filename, args.output_filename)

from collections import defaultdict
import argparse
import pathlib


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return ':' in uri or uri.count('_') >= 3


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


def reduce_assoc(dirname, cutoff=3, en_cutoff=4):
    path = pathlib.Path(dirname)
    counts = defaultdict(int)
    for filepath in path.glob('part_*.csv'):
        print(filepath)
        for line in filepath.open(encoding='utf-8'):
            left, right, value = line.rstrip().split('\t')
            if not concept_is_bad(left) and not concept_is_bad(right):
                counts[left] += 1
                counts[right] += 1

    filtered_concepts = {
        key for (key, value) in counts.items()
        if value >= en_cutoff
        or (not key.startswith('/c/en/')) and value >= cutoff
    }
    outpath = path / 'reduced.csv'
    with outpath.open('w', encoding='utf-8') as out:
        for filepath in path.glob('part_*.csv'):
            print("Re-reading %s" % filepath)
            for line in filepath.open(encoding='utf-8'):
                line = line.rstrip()
                left, right, value = line.split('\t')
                value = float(value)
                if left in filtered_concepts and right in filtered_concepts and value > 0:
                    print(line, file=out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')

    args = parser.parse_args()
    reduce_assoc(args.input_dir)

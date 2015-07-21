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


def reduce_assoc(dirname, cutoff=3, en_cutoff=4, verbose=True):
    """
    Removes uncommon associations and associations unlikely to be useful.
    This function expects files of the form part_*.csv in `dirname` and will
    create `reduced.csv` in `dirname`.

    All concepts that occur fewer than `cutoff` times will be removed.
    All english concepts that occur fewer than `en_cutoff` times will be removed
    """
    path = pathlib.Path(dirname)
    counts = defaultdict(int)
    for filepath in path.glob('part_*.csv'):
        if verbose:
            print(filepath)

        with filepath.open(encoding='utf-8') as file:
            for line in file:
                left, right, *_ = line.rstrip().split('\t')
                if not concept_is_bad(left) and not concept_is_bad(right):
                    counts[left] += 1
                    counts[right] += 1

    filtered_concepts = {
        concept for (concept, count) in counts.items()
        if count >= en_cutoff or
        not concept.startswith('/c/en/') and count >= cutoff
    }

    outpath = path / 'reduced.csv'
    with outpath.open('w', encoding='utf-8') as out:
        for filepath in path.glob('part_*.csv'):
            if verbose:
                print("Re-reading %s" % filepath)
            with filepath.open(encoding='utf-8') as file:
                for line in file:
                    left, right, value, *_ = line.rstrip().split('\t')
                    value = float(value)
                    if left in filtered_concepts and \
                        right in filtered_concepts and \
                        value != 0:
                        out.write(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')

    args = parser.parse_args()
    reduce_assoc(args.input_dir)

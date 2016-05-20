from collections import defaultdict
import argparse
from conceptnet5.uri import uri_prefixes


def concept_is_bad(uri):
    """
    Skip concepts that are unlikely to be useful.

    A concept containing too many underscores is probably a long, overly
    specific phrase, possibly mis-parsed. A concept with a colon is probably
    detritus from a wiki.
    """
    return ':' in uri or uri.count('_') >= 3 or uri.startswith('/a/') or uri.endswith('/neg')


def reduce_assoc(filename, output_filename, cutoff=4, en_cutoff=4, verbose=True):
    """
    Removes uncommon associations and associations unlikely to be useful.
    This function expects files of the form part_*.csv in `dirname` and will
    create `reduced.csv` in `dirname`.

    All concepts that occur fewer than `cutoff` times will be removed.
    All English concepts that occur fewer than `en_cutoff` times will be removed.
    """
    counts = defaultdict(int)
    with open(filename, encoding='utf-8') as file:
        for line in file:
            left, right, *_ = line.rstrip().split('\t')
            if not concept_is_bad(left) and not concept_is_bad(right):
                for prefix in uri_prefixes(left, 3):
                    counts[prefix] += 1
                for prefix in uri_prefixes(right, 3):
                    counts[prefix] += 1

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
                left, right, value, *_ = line.rstrip().split('\t')
                value = float(value)
                if (
                    left in filtered_concepts and right in filtered_concepts
                    and value != 0
                ):
                    out.write(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename')
    parser.add_argument('output_filename')

    args = parser.parse_args()
    reduce_assoc(args.input_filename, args.output_filename)


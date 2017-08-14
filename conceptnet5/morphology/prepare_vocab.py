import click
from conceptnet5.nodes import get_uri_language, split_uri
from conceptnet5.languages import ATOMIC_SPACE_LANGUAGES
from collections import defaultdict


def prepare_vocab_for_morphology(language, input, output):
    vocab_counts = defaultdict(int)
    for line in input:
        countstr, uri = line.strip().split(' ', 1)
        if get_uri_language(uri) == language:
            term = split_uri(uri)[2]
            if language in ATOMIC_SPACE_LANGUAGES:
                term += '_'
            vocab_counts[term] += int(countstr)

    for term, count in sorted(list(vocab_counts.items())):
        print(count, term, file=output)


@click.command()
@click.argument('language')
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w'))
def cli(language, input, output):
    prepare_vocab_for_morphology(language, input, output)


if __name__ == '__main__':
    cli()

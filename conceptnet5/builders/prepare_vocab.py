import click
from conceptnet5.nodes import get_uri_language, split_uri


# In Vietnamese, each space-separated token is a syllable, similar to a
# Chinese character. "bánh mì" is one word made of two syllables.
#
# What this means for Morfessor is that we have to handle Vietnamese, and any
# other language that turns out to have this property, differently. In most
# languages, a space means that there _must_ be a morpheme break here. In
# Vietnamese, spaces are the only places where there _may_ be a morpheme break,
# but not all spaces are morpheme breaks.
#
# In other words, in some languages, space-separated tokens are atomic. Which
# leads to this awesome, sci-fi-sounding constant name.
ATOMIC_SPACE_LANGUAGES = {'vi'}


def prepare_vocab_for_morphology(language, input, output):
    seen = set()
    for line in input:
        countstr, uri = line.strip().split(' ', 1)
        if get_uri_language(uri) == language:
            term = split_uri(uri)[2]
            if language in ATOMIC_SPACE_LANGUAGES:
                term += '_'
            if term not in seen:
                seen.add(term)
                print(term, file=output)


@click.command()
@click.argument('language')
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w'))
def cli(language, input, output):
    prepare_vocab_for_morphology(language, input, output)


if __name__ == '__main__':
    cli()

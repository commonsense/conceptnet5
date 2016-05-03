import click
from . import (
    conceptnet4, globalmind, jmdict, nadya, ptt_petgame, umbel, verbosity,
    wiktionary, wordnet
)


@click.group()
def cli():
    pass


@cli.command(name='conceptnet4')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='JSON-stream file of input'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_conceptnet4(input, output):
    conceptnet4.handle_file(input, output)


@cli.command(name='globalmind')
@click.argument('input_dir',
                type=click.Path(readable=True, dir_okay=True, file_okay=False),
                #help='directory containing GlobalMind exported data'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_globalmind(input_dir, output):
    globalmind.handle_file(input_dir, output)


@cli.command(name='jmdict')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='XML file containing JMDict'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_jmdict(input, output):
    jmdict.handle_file(input, output)


@cli.command(name='nadya')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='tab-separated data exported from nadya.jp'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_nadya(input, output):
    nadya.handle_file(input, output)


@cli.command(name='ptt_petgame')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='tab-separated data exported from the PTT Pet Game'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_ptt_petgame(input, output):
    ptt_petgame.handle_file(input, output)


@cli.command(name='umbel')
@click.argument('input_dir',
                type=click.Path(readable=True, dir_okay=True, file_okay=False),
                #help='directory containing Umbel data in N-Triples format'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
@click.option('--mapping', '-m', type=click.Path(writable=True, dir_okay=False),
              help='filename for a mapping from external Semantic Web URIs to ConceptNet URIs')
def run_umbel(input_dir, output, mapping):
    umbel.handle_file(input_dir, output, mapping)


@cli.command(name='verbosity')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='tab-separated data exported from Verbosity'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
def run_verbosity(input, output):
    verbosity.handle_file(input, output)


@cli.command(name='wiktionary_pre')
@click.argument('inputs', type=click.Path(readable=True, dir_okay=False),
                nargs=-1,
                #help='.jsons files of parsed Wiktionary data'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='SQLite DB to output to'
                )
def run_wiktionary_pre(inputs, output):
    wiktionary.prepare_db(inputs, output)


@cli.command(name='wordnet')
@click.argument('input', type=click.Path(readable=True, dir_okay=False),
                #help='WordNet RDF data in N-Triples format'
                )
@click.argument('output', type=click.Path(writable=True, dir_okay=False),
                #help='msgpack file to output to'
                )
@click.option('--mapping', '-m', type=click.Path(writable=True, dir_okay=False),
              #help='filename for a mapping from external Semantic Web URIs to ConceptNet URIs'
              )
def run_wordnet(input, output, mapping):
    wordnet.handle_file(input, output, mapping)

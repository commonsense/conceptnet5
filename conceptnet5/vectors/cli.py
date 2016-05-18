import click
from feather import read_dataframe, write_dataframe
from .formats import convert_glove, convert_word2vec
from .sparse_matrix_builder import build_from_conceptnet_table
from .retrofit import retrofit


@click.group()
def cli():
    pass


@cli.command(name='retrofit')
@click.argument('dense_hdf_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('conceptnet_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--iterations', '-i', default=10)
@click.option('--verbose', '-v', count=True)
def run_retrofit(dense_hdf_filename, conceptnet_filename, output_filename, iterations=10, verbose=1):
    dense_frame = read_dataframe(dense_hdf_filename)
    sparse_csr, combined_index = build_from_conceptnet_table(conceptnet_filename, orig_index=dense_frame.index)
    retrofitted = retrofit(combined_index, dense_frame, sparse_csr, iterations, verbose)
    write_dataframe(retrofitted, output_filename)


@cli.command(name='convert_glove')
@click.argument('glove_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nrows', '-n', default=500000)
def run_convert_glove(glove_filename, output_filename, nrows=500000):
    convert_glove(glove_filename, output_filename, nrows)


@cli.command(name='convert_word2vec')
@click.argument('word2vec_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nrows', '-n', default=500000)
def run_convert_word2vec(word2vec_filename, output_filename, nrows=500000):
    convert_word2vec(word2vec_filename, output_filename, nrows)

import click
from .formats import convert_glove, convert_word2vec, load_hdf, save_hdf
from .sparse_matrix_builder import build_from_conceptnet_table
from .retrofit import sharded_retrofit, join_shards
from .interpolate import merge_intersect
from .evaluation.wordsim import evaluate, evaluate_raw
from .transforms import shrink_and_sort
from .query import VectorSpaceWrapper


@click.group()
def cli():
    pass

@cli.command(name='filter_word_vectors')
@click.argument('dense_hdf_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('vocab_filename', type=click.Path(readable=True, dir_okay=False))
def filter_word_vectors(dense_hdf_filename, vocab_filename):
    vsw = VectorSpaceWrapper(vector_filename=dense_hdf_filename)
    for line in open(vocab_filename):
        word = line.strip()
        term = '/c/en/' + word
        vec = vsw.get_vector(term)
        line_parts = [word] + ['%6.6f' % num for num in vec]
        print(' '.join(line_parts))


@cli.command(name='retrofit')
@click.argument('dense_hdf_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('conceptnet_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--iterations', '-i', default=5)
@click.option('--verbose', '-v', count=True)
@click.option('--nshards', '-s', default=6)
def run_retrofit(dense_hdf_filename, conceptnet_filename, output_filename,
                 iterations=5, nshards=6, verbose=1):
    sharded_retrofit(
        dense_hdf_filename, conceptnet_filename, output_filename,
        iterations=iterations, nshards=nshards, verbose=verbose
    )


@cli.command(name='join_retrofit')
@click.argument('filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nshards', '-s', default=6)
def run_join_retrofit(filename, nshards=6):
    join_shards(filename, nshards)


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


@cli.command(name='intersect')
@click.argument('input_filenames', nargs=-1, type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.argument('projection_filename', type=click.Path(writable=True, dir_okay=False))
def run_intersect(input_filenames, output_filename, projection_filename):
    frames = [load_hdf(filename) for filename in input_filenames]
    intersected, projection = merge_intersect(frames)
    save_hdf(intersected, output_filename)
    save_hdf(projection, projection_filename)


@cli.command(name='evaluate')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
def run_evaluate(filename):
    frame = load_hdf(filename)
    print(evaluate(frame))


@cli.command(name='evaluate_raw')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
def run_evaluate(filename):
    frame = load_hdf(filename)
    print(evaluate_raw(frame))


@cli.command(name='shrink')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('-n', default=1000000, help="Number of rows to truncate to")
@click.option('-k', default=300, help="Number of columns to truncate to")
def run_shrink(input_filename, output_filename, n, k):
    frame = load_hdf(input_filename)
    shrunk = shrink_and_sort(frame, n, k)
    save_hdf(shrunk, output_filename)

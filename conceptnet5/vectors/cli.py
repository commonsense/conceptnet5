import click
from .formats import (
    convert_glove, convert_word2vec, convert_fasttext, load_hdf, save_hdf,
    export_conceptnet_to_hyperwords, export_plain_text
)
from .retrofit import sharded_retrofit, join_shards
from .merge import merge_intersect
from .evaluation.wordsim import evaluate, evaluate_raw
from .evaluation.compare import compare_embeddings, graph_comparison
from .transforms import miniaturize
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


@cli.command(name='convert_fasttext')
@click.argument('fasttext_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nrows', '-n', default=500000)
def run_convert_fasttext(fasttext_filename, output_filename, nrows=500000):
    convert_fasttext(fasttext_filename, output_filename, nrows)


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
@click.option('--subset', '-s', type=click.Choice(['dev', 'test', 'all']), default='dev')
def run_evaluate(filename, subset):
    frame = load_hdf(filename)
    print(evaluate(frame, subset=subset))


@cli.command(name='evaluate_raw')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
def run_evaluate_raw(filename):
    frame = load_hdf(filename)
    print(evaluate_raw(frame))


@cli.command(name='compare_embeddings')
@click.argument('input_filenames', nargs=-1, type=click.Path(readable=True, dir_okay=False))
@click.argument('psql_file_check', type=click.Path())
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
def run_compare_embeddings(input_filenames, psql_file_check, output_filename):
    """
    The `input_filenames` are files that can be loaded as matrices of word
    embeddings. They'll be run through the relatedness and analogy evaluations,
    and the results will be saved in an HDF5 file, `output_filename`. This
    file can be used by `comparison_graph`.

    This requires the PostgreSQL database of ConceptNet 5 to be built, because
    it finds embeddings of uncommon words on the fly by looking up their
    neighbors in the ConceptNet graph. These embeddings could have been stored
    in the matrix, but this saves memory and download time.

    The `psql_file_check` argument is ignored; it's just a convenient way
    to make Snakemake realize that the PostgreSQL database has to be available.
    """
    results = compare_embeddings(input_filenames, subset='all', tune_analogies=True)
    print(results['acc'])
    save_hdf(results, output_filename)


@cli.command(name='comparison_graph')
@click.argument('table_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('out_filename', type=click.Path(writable=True, dir_okay=False))
def run_comparison_graph(table_filename, out_filename):
    """
    Convert a table of evaluation results into a PNG or PDF graph.
    """
    graph_comparison(table_filename, out_filename)


@cli.command(name='export_hyperwords')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_matrix', type=click.Path(writable=True, dir_okay=False))
@click.argument('output_vocab', type=click.Path(writable=True, dir_okay=False))
@click.option('--nrows', '-n', default=200000)
def run_export_hyperwords(input_filename, output_matrix, output_vocab, nrows=200000):
    frame = load_hdf(input_filename)
    export_conceptnet_to_hyperwords(frame, output_matrix, output_vocab, nrows=nrows)


@cli.command(name='export_text')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('uri_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_dir', type=click.Path(writable=True, dir_okay=True, file_okay=False))
def run_export(input_filename, uri_filename, output_dir):
    frame = load_hdf(input_filename)
    export_plain_text(frame, uri_filename, output_dir)


@cli.command(name='miniaturize')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('extra_vocab_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('-k', default=256, help="Number of columns to reduce to")
def run_miniaturize(input_filename, extra_vocab_filename, output_filename, k):
    frame = load_hdf(input_filename)
    other_frame = load_hdf(extra_vocab_filename)
    other_vocab = list(other_frame.index)
    del other_frame
    mini = miniaturize(frame, other_vocab=other_vocab, k=k)
    save_hdf(mini, output_filename)

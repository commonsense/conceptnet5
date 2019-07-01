from os import path

import click

from .debias import de_bias_frame
from .evaluation import analogy, bias, wordsim
from .evaluation.compare import compare_embeddings, graph_comparison
from .formats import (
    convert_fasttext,
    convert_glove,
    convert_polyglot,
    convert_word2vec,
    export_text,
    load_hdf,
    save_hdf,
    save_labels,
    save_npy,
)
from .merge import merge_intersect
from .miniaturize import miniaturize
from .propagate import sharded_propagate
from .query import VectorSpaceWrapper
from .retrofit import join_shards, sharded_retrofit
from .transforms import make_big_frame, make_small_frame

ANALOGY_FILENAME = 'data/raw/analogy/SAT-package-V3.txt'


@click.group()
def cli():
    pass


@cli.command(name='filter_word_vectors')
@click.argument('dense_hdf_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('vocab_filename', type=click.Path(readable=True, dir_okay=False))
def filter_word_vectors(dense_hdf_filename, vocab_filename):
    """
    Get embeddings for the words in vocab_filename.
    """
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
@click.option('--nshards', '-n', default=6)
@click.option('--verbose', '-v', count=True)
@click.option('--max_cleanup_iters', '-m', default=20)
@click.option('--orig_vec_weight', '-w', default=0.15)
def run_retrofit(
    dense_hdf_filename,
    conceptnet_filename,
    output_filename,
    iterations=5,
    nshards=6,
    verbose=0,
    max_cleanup_iters=20,
    orig_vec_weight=0.15,
):
    """
    Run retrofit, operating on a part of a frame at a time.
    """
    sharded_retrofit(
        dense_hdf_filename,
        conceptnet_filename,
        output_filename,
        iterations=iterations,
        nshards=nshards,
        verbosity=verbose,
        max_cleanup_iters=max_cleanup_iters,
        orig_vec_weight=orig_vec_weight,
    )


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
@click.option('--language', '-l', default='en')
def run_convert_fasttext(
    fasttext_filename, output_filename, nrows=500000, language='en'
):
    convert_fasttext(fasttext_filename, output_filename, nrows=nrows, language=language)


@cli.command(name='convert_word2vec')
@click.argument('word2vec_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nrows', '-n', default=500000)
def run_convert_word2vec(word2vec_filename, output_filename, nrows=500000):
    convert_word2vec(word2vec_filename, output_filename, nrows)


@cli.command(name='convert_polyglot')
@click.argument('polyglot_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--language', '-l')
def run_convert_polyglot(polyglot_filename, output_filename, language):
    convert_polyglot(polyglot_filename, output_filename, language)


@cli.command(name='intersect')
@click.argument(
    'input_filenames', nargs=-1, type=click.Path(readable=True, dir_okay=False)
)
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.argument('projection_filename', type=click.Path(writable=True, dir_okay=False))
def run_intersect(input_filenames, output_filename, projection_filename):
    """
    Combine the vector knowledge contained in frames.
    """
    intersected, projection = merge_intersect(input_filenames)
    save_hdf(intersected, output_filename)
    save_hdf(projection, projection_filename)


@cli.command(name='debias')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
def run_debias(input_filename, output_filename):
    """
    Modify a frame to attempt to remove biases and prejudices.
    """
    frame = load_hdf(input_filename)
    de_bias_frame(frame)
    save_hdf(frame, output_filename)


@cli.command(name='evaluate')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
@click.option(
    '--subset', '-s', type=click.Choice(['dev', 'test', 'all']), default='dev'
)
@click.option('--semeval-by-language/--semeval-global', '-l', default=False)
@click.option('--run-analogies', is_flag=True)
def run_evaluate(filename, subset, semeval_by_language, run_analogies):
    """
    Evaluate a frame on word similarity and (optionally) analogy tasks. Measure its bias.
    """
    frame = load_hdf(filename)
    if semeval_by_language:
        scope = 'per-language'
    else:
        scope = 'global'
    print(wordsim.evaluate(frame, subset=subset, semeval_scope=scope))
    if run_analogies:
        print(analogy.evaluate(frame, subset=subset, analogy_filename=ANALOGY_FILENAME))
    print(bias.measure_bias(frame))


@cli.command(name='evaluate_wordsim')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
@click.option(
    '--subset', '-s', type=click.Choice(['dev', 'test', 'all']), default='dev'
)
@click.option('--semeval-by-language/--semeval-global', '-l', default=False)
def run_evaluate_wordsim(filename, subset, semeval_by_language):
    """
    Evaluate a frame on word similarity tasks. Include OOV handling.
    """
    frame = load_hdf(filename)
    if semeval_by_language:
        scope = 'per-language'
    else:
        scope = 'global'
    print(wordsim.evaluate(frame, subset=subset, semeval_scope=scope))


@cli.command(name='evaluate_raw')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
@click.option(
    '--subset', '-s', type=click.Choice(['dev', 'test', 'all']), default='dev'
)
@click.option('--semeval-by-language/--semeval-global', '-l', default=False)
def run_evaluate_raw(filename, subset, semeval_by_language):
    """
    Evaluate a frame on word similarity tasks. Do not include OOV handling.
    """
    frame = load_hdf(filename)
    if semeval_by_language:
        scope = 'per-language'
    else:
        scope = 'global'
    print(wordsim.evaluate_raw(frame, subset=subset, semeval_scope=scope))


@cli.command(name='evaluate_analogies')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
@click.option(
    '--subset', '-s', type=click.Choice(['dev', 'test', 'all']), default='dev'
)
def run_evaluate_analogies(filename, subset):
    """
    Evaluate a frame on analogy datasets: SAT, Google analogies, Semeval2012-Task2.
    """
    frame = load_hdf(filename)
    print(analogy.evaluate(frame, subset=subset, analogy_filename=ANALOGY_FILENAME))


@cli.command(name='evaluate_bias')
@click.argument('filename', type=click.Path(readable=True, dir_okay=False))
def run_evaluate_bias(filename):
    """
    Measure bias in a given frame.
    """
    frame = load_hdf(filename)
    print(bias.measure_bias(frame))


@cli.command(name='compare_embeddings')
@click.argument(
    'input_filenames', nargs=-1, type=click.Path(readable=True, dir_okay=False)
)
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--run-analogies', is_flag=True)
def run_compare_embeddings(input_filenames, output_filename, run_analogies):
    """
    The `input_filenames` are files that can be loaded as matrices of word
    embeddings. They'll be run through the relatedness and analogy evaluations,
    and the results will be saved in an HDF5 file, `output_filename`. This
    file can be used by `comparison_graph`.

    This requires the PostgreSQL database of ConceptNet 5 to be built, because
    it finds embeddings of uncommon words on the fly by looking up their
    neighbors in the ConceptNet graph. These embeddings could have been stored
    in the matrix, but this saves memory and download time.
    """
    results = compare_embeddings(
        input_filenames, subset='all', run_analogies=run_analogies
    )
    print(results)
    save_hdf(results, output_filename)


@cli.command(name='comparison_graph')
@click.argument('table_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('eval_graph_filename', type=click.Path(writable=True, dir_okay=False))
def run_comparison_graph(table_filename, eval_graph_filename):
    """
    Convert a table of evaluation results into a PNG or PDF graph.
    """
    graph_comparison(table_filename, eval_graph_filename)


@cli.command(name='export_text')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--language', '-l', default=None)
def run_export(input_filename, output_filename, language):
    """
    Export a frame to a fastText-style text file.
    """
    frame = load_hdf(input_filename)
    export_text(frame, output_filename, language)


@cli.command(name='miniaturize')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('extra_vocab_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('-k', default=300, help="Number of columns to reduce to")
def run_miniaturize(input_filename, extra_vocab_filename, output_filename, k):
    """
    Save a smaller version of a frame, which includes frequent terms and phrases.
    """
    frame = load_hdf(input_filename)
    other_frame = load_hdf(extra_vocab_filename)
    other_vocab = list(other_frame.index)
    del other_frame
    mini = miniaturize(frame, other_vocab=other_vocab, k=k)
    save_hdf(mini, output_filename)


@cli.command(name='export_background')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_dir', type=click.Path(writable=True, dir_okay=True))
@click.argument('concepts_filename', type=click.Path(readable=True, dir_okay=False))
@click.option('-l', '--language', default='en')
def export_background(input_filename, output_dir, concepts_filename, language):
    concepts = set(line.strip() for line in open(concepts_filename))
    frame = load_hdf(input_filename)
    big_frame = make_big_frame(frame, language)
    small_frame = make_small_frame(big_frame, concepts)

    # save labels
    labels_filename = path.join(output_dir, 'labels.txt')
    save_labels(small_frame, labels_filename)

    # save small_frame matrix
    vectors_filename = path.join(output_dir, 'vectors.npy')
    save_npy(small_frame.values, vectors_filename)


@cli.command(name='propagate')
@click.argument('assoc_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('embedding_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nshards', '-n', default=6)
@click.option('--iterations', default=20)
def run_propagate(
    assoc_filename, embedding_filename, output_filename, nshards=6, iterations=20
):
    sharded_propagate(
        assoc_filename,
        embedding_filename,
        output_filename,
        nshards=nshards,
        iterations=iterations,
    )


@cli.command(name='join_shard_files')
@click.argument('filename', type=click.Path(writable=True, dir_okay=False))
@click.option('--nshards', '-n', default=6)
@click.option('--sort/--no-sort', default=False)
def run_join_shard_files(filename, nshards=6, sort=False):
    """
    Join parts of a sharded (e.g. from retrofitting or propagation) frame.
    """
    join_shards(filename, nshards, sort=sort)

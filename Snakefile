from snakemake.remote.HTTP import RemoteProvider as HTTPRemoteProvider
import os
HTTP = HTTPRemoteProvider()

# The directory containing the data files. By default, this is "data" under
# the current directory, but it can be overridden using the
# CONCEPTNET_BUILD_DATA environment variable. This will happen during testing.
DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "data")

# Some build steps are difficult to run, so we've already run them and put
# the results in S3. Of course, that can't be the complete solution, because
# we have to have run those build steps first. So when USE_PRECOMPUTED is
# True, we will download the computed files; when it's False, we will compute
# them.
USE_PRECOMPUTED = not os.environ.get("CONCEPTNET_REBUILD_PRECOMPUTED")

# If USE_PRECOMPUTED is False, should we upload the files we compute so they
# can be used as precomputed files later? (Requires ConceptNet S3 credentials.)
UPLOAD = False

# How many pieces to split edge files into. (Works best when it's a power of
# 2 that's 64 or less.)
N_PIECES = 16

# The versions of Wiktionary data to download. Updating these requires
# uploading new Wiktionary dumps to ConceptNet's S3.
WIKTIONARY_VERSIONS = {
    'en': '20160305',
    'fr': '20160305',
    'de': '20160407'
}
WIKTIONARY_LANGUAGES = sorted(list(WIKTIONARY_VERSIONS))

# Languages where morphemes should not be split anywhere except at spaces
ATOMIC_SPACE_LANGUAGES = {'vi'}

# Languages that the CLDR emoji data is available in. These match the original
# filenames, not ConceptNet language codes; they are turned into ConceptNet
# language codes by the reader.
EMOJI_LANGUAGES = [
    'af', 'am', 'ar', 'as', 'az', 'be', 'bg', 'bn', 'bs', 'ca', 'cs', 'cy',
    'da', 'de', 'de_CH', 'el', 'en', 'en_001', 'es', 'es_419', 'et', 'eu',
    'fa', 'fi', 'fil', 'fr', 'ga', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy',
    'id', 'is', 'it', 'ja', 'ka', 'kk', 'km', 'kn', 'ko', 'ky', 'lo', 'lt',
    'lv', 'mk', 'ml', 'mn', 'mr', 'ms', 'my', 'nb', 'ne', 'nl', 'or', 'pa',
    'pl', 'pt', 'pt_PT', 'ro', 'ru', 'si', 'sk', 'sl', 'sq', 'sr', 'sr_Latn',
    'sv', 'sw', 'ta', 'te', 'th', 'tr', 'uk', 'ur', 'uz', 'vi', 'zh',
    'zh_Hant', 'zu'
]

# Increment this number when we incompatibly change the parser
WIKT_PARSER_VERSION = "1"

RETROFIT_SHARDS = 6

# Dataset filenames
# =================
# The goal of reader steps is to produce Msgpack files, and later CSV files,
# with these names.
#
# We distingish *core dataset names*, which collectively determine the set of
# terms that ConceptNet will attempt to represent, from the additional datasets
# that will mainly be used to find more information about those terms.


RAW_DATA_URL = "https://zenodo.org/record/998169/files/conceptnet-raw-data-5.5.zip"
PRECOMPUTED_DATA_PATH = "/precomputed-data/2016"
PRECOMPUTED_DATA_URL = "https://conceptnet.s3.amazonaws.com" + PRECOMPUTED_DATA_PATH
PRECOMPUTED_S3_UPLOAD = "s3://conceptnet" + PRECOMPUTED_DATA_PATH

INPUT_EMBEDDINGS = [
    'glove12-840B', 'w2v-google-news', 'fasttext-opensubtitles'
]
SOURCE_EMBEDDING_ROWS = 1500000
MULTILINGUAL_SOURCE_EMBEDDING_ROWS = 2000000

# If CONCEPTNET_BUILD_TEST is set, we're running the small test build.
TESTMODE = bool(os.environ.get("CONCEPTNET_BUILD_TEST"))
if TESTMODE:
    # Use a throwaway database to store the ConceptNet data when testing
    os.environ['CONCEPTNET_DB_NAME'] = 'conceptnet-test'

    # Retrofit a tiny version of GloVe when testing
    INPUT_EMBEDDINGS = ['glove12-840B']
    SOURCE_EMBEDDING_ROWS = 5000

    DATA = "testdata"
    USE_PRECOMPUTED = True
    HASH_WIDTH = 12
    RAW_DATA_URL = "/missing/data"
    PRECOMPUTED_DATA_URL = "/missing/data"
    EMOJI_LANGUAGES = ['en', 'en_001']


CORE_DATASET_NAMES = [
    "jmdict/jmdict",
    "nadya/nadya",
    "ptt_petgame/api",
    "opencyc/opencyc",
    "verbosity/verbosity",
    "wordnet/wordnet",
    "cedict/cedict"
]
CORE_DATASET_NAMES += ["conceptnet4/conceptnet4_flat_{}".format(num) for num in range(10)]
CORE_DATASET_NAMES += ["ptt_petgame/part{}".format(num) for num in range(1, 13)]
CORE_DATASET_NAMES += ["wiktionary/{}".format(lang) for lang in WIKTIONARY_LANGUAGES]
CORE_DATASET_NAMES += ["emoji/{}".format(lang) for lang in EMOJI_LANGUAGES]


DATASET_NAMES = CORE_DATASET_NAMES + ["dbpedia/dbpedia_en"]


rule all:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/psql/edges.csv.gz",
        DATA + "/psql/edge_sources.csv.gz",
        DATA + "/psql/edge_features.csv.gz",
        DATA + "/psql/nodes.csv.gz",
        DATA + "/psql/node_prefixes.csv.gz",
        DATA + "/psql/sources.csv.gz",
        DATA + "/psql/relations.csv.gz",
        DATA + "/psql/done",
        DATA + "/stats/languages.txt",
        DATA + "/stats/language_edges.txt",
        DATA + "/stats/relations.txt",
        DATA + "/assoc/reduced.csv",
        DATA + "/vectors/mini.h5"

rule evaluation:
    input:
        DATA + "/stats/eval-graph.png"

rule webdata:
    input:
        DATA + "/psql/edges.csv.gz",
        DATA + "/psql/edge_sources.csv.gz",
        DATA + "/psql/edge_features.csv.gz",
        DATA + "/psql/nodes.csv.gz",
        DATA + "/psql/node_prefixes.csv.gz",
        DATA + "/psql/sources.csv.gz",
        DATA + "/psql/relations.csv.gz",
        DATA + "/psql/done",
        DATA + "/vectors/mini.h5",

rule clean:
    shell:
        "for subdir in assertions assoc collated db edges psql tmp vectors stats; "
        "do echo Removing {DATA}/$subdir; "
        "rm -rf {DATA}/$subdir; done"

rule test:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/psql/done",
        DATA + "/assoc/reduced.csv",
        DATA + "/vectors/plain/numberbatch-en.txt.gz",


# Downloaders
# ===========
rule download_raw_package:
    output:
        DATA + "/raw/conceptnet-raw-data-5.5.zip"
    shell:
        "wget -nv {RAW_DATA_URL} -O {output}"

rule extract_raw:
    input:
        DATA + "/raw/conceptnet-raw-data-5.5.zip"
    output:
        DATA + "/raw/{dirname}/{filename}"
    shell:
        "unzip {input} raw/{wildcards.dirname}/{wildcards.filename} -d {DATA}"

rule download_conceptnet_ppmi:
    output:
        DATA + "/precomputed/vectors/conceptnet-55-ppmi.h5"
    shell:
        "wget -nv {PRECOMPUTED_DATA_URL}/numberbatch/16.09/conceptnet-55-ppmi.h5 -O {output}"

rule download_numberbatch:
    output:
        DATA + "/precomputed/vectors/numberbatch.h5"
    shell:
        "wget -nv {PRECOMPUTED_DATA_URL}/numberbatch/16.09/numberbatch.h5 -O {output}"

rule download_opensubtitles_ppmi:
    output:
        DATA + "/precomputed/vectors/opensubtitles-ppmi-5.h5"
    shell:
        "wget -nv {PRECOMPUTED_DATA_URL}/numberbatch/17.02/opensubtitles-ppmi-5.h5 -O {output}"


# Precomputation
# ==============
# This section is for tricky build steps where we would rather just distribute
# the result of the computation.

def find_wiktionary_input(wildcards):
    if USE_PRECOMPUTED:
        return []
    else:
        language = wildcards.language
        version = WIKTIONARY_VERSIONS[wildcards.language]
        filename = DATA + "/raw/wiktionary/{0}wiktionary-{1}-pages-articles.xml.bz2".format(
            language, version
        )
        return [filename]

rule precompute_wiktionary:
    input:
        find_wiktionary_input
    output:
        DATA + "/precomputed/wiktionary/parsed-{version}/{language}.jsons.gz"
    run:
        if USE_PRECOMPUTED:
            shell("wget {PRECOMPUTED_DATA_URL}/wiktionary/"
                  "parsed-{wildcards.version}/{wildcards.language}.jsons.gz "
                  "-O {output}")
        else:
            # This is a mess because, for most of these sub-steps, the file
            # being output isn't {output} but its uncompressed version
            shell("bunzip2 -c {input} "
                  "| wiktionary-parser {wildcards.language} "
                  "| gzip -c > {output}")
            if UPLOAD:
                shell("aws s3 cp {output} "
                    "{PRECOMPUTED_S3_UPLOAD}/wiktionary/"
                    "parsed-{wildcards.version}/{wildcards.language}.jsons.gz "
                    "--acl public-read")


# Readers
# =======
# These are steps that turn raw data into files of uncombined 'edges'.

rule read_conceptnet4:
    input:
        DATA + "/raw/conceptnet4/conceptnet4_flat_{num}.jsons",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    run:
        single_input = input[0]
        shell("cn5-read conceptnet4 {single_input} {output}")

rule read_dbpedia:
    input:
        DATA + "/raw/dbpedia/instance_types_en.tql.bz2",
        DATA + "/raw/dbpedia/interlanguage_links_en.tql.bz2",
        DATA + "/raw/dbpedia/mappingbased_objects_en.tql.bz2",
        DATA + "/stats/core_concepts.txt"
    output:
        DATA + "/edges/dbpedia/dbpedia_en.msgpack",
    shell:
        "cn5-read dbpedia {DATA}/raw/dbpedia "
        "{output} "
        "{DATA}/stats/core_concepts.txt "

rule read_jmdict:
    input:
        DATA + "/raw/jmdict/JMdict.xml"
    output:
        DATA + "/edges/jmdict/jmdict.msgpack"
    shell:
        "cn5-read jmdict {input} {output}"

rule read_nadya:
    input:
        DATA + "/raw/nadya/nadya-2014.csv"
    output:
        DATA + "/edges/nadya/nadya.msgpack"
    shell:
        "cn5-read nadya {input} {output}"

rule read_ptt_petgame:
    input:
        DATA + "/raw/ptt_petgame/conceptnet_zh_{part}.txt"
    output:
        DATA + "/edges/ptt_petgame/{part}.msgpack"
    shell:
        "cn5-read ptt_petgame {input} {output}"

rule read_opencyc:
    input:
        DATA + "/raw/opencyc/opencyc-2012-05-10-readable.nq"
    output:
        DATA + "/edges/opencyc/opencyc.msgpack"
    shell:
        "cn5-read opencyc {input} {output}"

rule read_verbosity:
    input:
        DATA + "/raw/verbosity/verbosity.txt"
    output:
        DATA + "/edges/verbosity/verbosity.msgpack"
    shell:
        "cn5-read verbosity {input} {output}"

rule prescan_wiktionary:
    input:
        expand(
            DATA + "/precomputed/wiktionary/parsed-{version}/{language}.jsons.gz",
            version=[WIKT_PARSER_VERSION],
            language=WIKTIONARY_LANGUAGES
        )
    output:
        DATA + "/db/wiktionary.db"
    shell:
        "mkdir -p {DATA}/tmp && "
        "cn5-read wiktionary_pre {input} {DATA}/tmp/wiktionary.db && "
        "mv {DATA}/tmp/wiktionary.db {output}"

rule read_wiktionary:
    input:
        DATA + "/precomputed/wiktionary/parsed-%s/{language}.jsons.gz" % WIKT_PARSER_VERSION,
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/edges/wiktionary/{language}.msgpack",
    shell:
        "cn5-read wiktionary {input} {output}"

rule read_wordnet:
    input:
        DATA + "/raw/wordnet-rdf/wn31.nt"
    output:
        DATA + "/edges/wordnet/wordnet.msgpack",
    shell:
        "cn5-read wordnet {input} {output}"

rule read_emoji:
    input:
        DATA + "/raw/emoji/{language}.xml"
    output:
        DATA + "/edges/emoji/{language}.msgpack"
    shell:
        "cn5-read emoji {input} {output}"

rule read_cc_cedict:
    input:
        DATA + "/raw/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
    output:
        DATA + "/edges/cedict/cedict.msgpack",
    shell:
        "cn5-read cc_cedict {input} {output}"


# Converting msgpack to csv
# =========================

rule edge_msgpack_to_csv:
    input:
        DATA + "/edges/{dir}/{filename}.msgpack"
    output:
        DATA + "/edges/{dir,[^/]+}/{filename}.csv"
    shell:
        "cn5-convert msgpack_to_tab_separated {input} {output}"

rule assertion_msgpack_to_csv:
    input:
        DATA + "/assertions/{filename}.msgpack"
    output:
        DATA + "/assertions/{filename}.csv"
    shell:
        "cn5-convert msgpack_to_tab_separated {input} {output}"

rule sort_edges:
    input:
        expand(DATA + "/edges/{dataset}.csv", dataset=DATASET_NAMES)
    output:
        DATA + "/collated/sorted/edges.csv"
    shell:
        "mkdir -p {DATA}/tmp && cat {input} | LC_ALL=C sort -T {DATA}/tmp | LC_ALL=C uniq > {output}"

rule combine_assertions:
    input:
        DATA + "/collated/sorted/edges.csv"
    output:
        DATA + "/assertions/assertions.msgpack"
    shell:
        "python3 -m conceptnet5.builders.combine_assertions {input} {output}"


# Putting data in PostgreSQL
# ==========================
rule prepare_db:
    input:
        DATA + "/assertions/assertions.msgpack"
    output:
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_sources.csv",
        DATA + "/psql/edge_features.csv",
        DATA + "/psql/nodes.csv",
        DATA + "/psql/node_prefixes.csv",
        DATA + "/psql/sources.csv",
        DATA + "/psql/relations.csv"
    shell:
        "cn5-db prepare_data {input} {DATA}/psql"

rule gzip_db:
    input:
        DATA + "/psql/{name}.csv"
    output:
        DATA + "/psql/{name}.csv.gz"
    shell:
        "gzip -c {input} > {output}"

rule load_db:
    input:
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_sources.csv",
        DATA + "/psql/edge_features.csv",
        DATA + "/psql/nodes.csv",
        DATA + "/psql/node_prefixes.csv",
        DATA + "/psql/sources.csv",
        DATA + "/psql/relations.csv"
    output:
        DATA + "/psql/done"
    shell:
        "cn5-db load_data {DATA}/psql && touch {output}"


# Collecting statistics
# =====================
rule relation_stats:
    input:
        DATA + "/assertions/assertions.csv"
    output:
        DATA + "/stats/relations.txt"
    shell:
        "cut -f 2 {input} | LC_ALL=C sort | LC_ALL=C uniq -c "
        "| LC_ALL=C sort -nbr > {output}"

rule all_terms:
    input:
        DATA + "/psql/nodes.csv"
    output:
        DATA + "/stats/terms.txt"
    shell:
        "cut -f 2 {input} > {output}"

rule core_concepts_left:
    input:
        expand(DATA + "/edges/{dataset}.csv", dataset=CORE_DATASET_NAMES)
    output:
        DATA + "/stats/core_concepts_left.txt"
    shell:
        "cut -f 3 {input} > {output}"

rule core_concepts_right:
    input:
        expand(DATA + "/edges/{dataset}.csv", dataset=CORE_DATASET_NAMES)
    output:
        DATA + "/stats/core_concepts_right.txt"
    shell:
        "cut -f 3 {input} > {output}"

rule core_concepts:
    input:
        DATA + "/stats/core_concepts_left.txt",
        DATA + "/stats/core_concepts_right.txt"
    output:
        DATA + "/stats/core_concepts.txt"
    shell:
        "LC_ALL=C sort -u {input} > {output}"


rule concepts_left:
    input:
        DATA + "/assertions/assertions.csv"
    output:
        DATA + "/stats/concepts_left.txt"
    shell:
        "cut -f 3 {input} > {output}"

rule concepts_right:
    input:
        DATA + "/assertions/assertions.csv"
    output:
        DATA + "/stats/concepts_right.txt"
    shell:
        "cut -f 4 {input} > {output}"


rule language_stats:
    input:
        DATA + "/stats/concepts_left.txt",
        DATA + "/stats/concepts_right.txt"
    output:
        DATA + "/stats/languages.txt"
    shell:
        "cat {input} | grep '^/c/' | LC_ALL=C sort | LC_ALL=C uniq | cut -d '/' -f 3 "
        "| LC_ALL=C sort | LC_ALL=C uniq -c | sort -nbr > {output}"

rule language_edge_stats:
    input:
        DATA + "/stats/concepts_left.txt",
        DATA + "/stats/concepts_right.txt"
    output:
        DATA + "/stats/language_edges.txt"
    shell:
        "cat {input} | grep '^/c/' | LC_ALL=C sort | cut -d '/' -f 3 "
        "| LC_ALL=C sort | LC_ALL=C uniq -c | sort -nbr > {output}"


# Building associations
# =====================
rule assertions_to_assoc:
    input:
        DATA + "/assertions/assertions.msgpack"
    output:
        DATA + "/assoc/assoc-with-dups.csv"
    shell:
        "cn5-convert msgpack_to_assoc {input} {output}"

rule assoc_uniq:
    input:
        DATA + "/assoc/assoc-with-dups.csv"
    output:
        DATA + "/assoc/assoc.csv"
    shell:
        "LC_ALL=C sort {input} | LC_ALL=C uniq > {output}"

rule reduce_assoc:
    input:
        DATA + "/assoc/assoc.csv"
    output:
        DATA + "/assoc/reduced.csv"
    shell:
        "python3 -m conceptnet5.builders.reduce_assoc {input} {output}"


# Building the vector space
# =========================
rule convert_word2vec:
    input:
        DATA + "/raw/vectors/GoogleNews-vectors-negative300.bin.gz"
    output:
        DATA + "/vectors/w2v-google-news.h5"
    resources:
        ram=24
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_word2vec -n {SOURCE_EMBEDDING_ROWS} {input} {output}"

rule convert_glove:
    input:
        DATA + "/raw/vectors/glove12.840B.300d.txt.gz"
    output:
        DATA + "/vectors/glove12-840B.h5"
    resources:
        ram=24
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_glove -n {SOURCE_EMBEDDING_ROWS} {input} {output}"

rule convert_fasttext:
    input:
        DATA + "/raw/vectors/fasttext-wiki-{lang}.vec.gz"
    output:
        DATA + "/vectors/fasttext-wiki-{lang}.h5"
    resources:
        ram=24
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {SOURCE_EMBEDDING_ROWS} -l {wildcards.lang} {input} {output}"

rule convert_lexvec:
    input:
        DATA + "/raw/vectors/lexvec.commoncrawl.300d.W+C.pos.vectors.gz",
    output:
        DATA + "/vectors/lexvec-commoncrawl.h5"
    resources:
        ram=24
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {SOURCE_EMBEDDING_ROWS} {input} {output}"

rule convert_opensubtitles_ft:
    input:
        DATA + "/raw/vectors/ft-opensubtitles.vec.gz",
    output:
        DATA + "/vectors/fasttext-opensubtitles.h5"
    resources:
        ram=24
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {MULTILINGUAL_SOURCE_EMBEDDING_ROWS} {input} {output}"

rule convert_polyglot:
    input:
        DATA + "/raw/vectors/polyglot-{language}.pkl"
    output:
        DATA + "/vectors/polyglot-{language}.h5"
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_polyglot -l {wildcards.language} {input} {output}"

rule import_opensubtitles_ppmi:
    input:
        DATA + "/precomputed/vectors/opensubtitles-ppmi-5.h5"
    output:
        DATA + "/vectors/opensubtitles-ppmi-5.h5"
    shell:
        "cp {input} {output}"

rule retrofit:
    input:
        DATA + "/vectors/{name}.h5",
        DATA + "/assoc/reduced.csv"
    output:
        temp(expand(DATA + "/vectors/{{name}}-retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS)))
    resources:
        ram=24
    shell:
        "cn5-vectors retrofit -s {RETROFIT_SHARDS} {input} {DATA}/vectors/{wildcards.name}-retrofit.h5"

rule join_retrofit:
    input:
        expand(DATA + "/vectors/{{name}}-retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS))
    output:
        DATA + "/vectors/{name}-retrofit.h5"
    resources:
        ram=24
    shell:
        "cn5-vectors join_retrofit -s {RETROFIT_SHARDS} {output}"

rule merge_intersect:
    input:
        expand(DATA + "/vectors/{name}-retrofit.h5", name=INPUT_EMBEDDINGS)
    output:
        DATA + "/vectors/numberbatch-biased.h5",
        DATA + "/vectors/intersection-projection.h5"
    resources:
        ram=24
    shell:
        "cn5-vectors intersect {input} {output}"

rule debias:
    input:
        DATA + "/vectors/numberbatch-biased.h5"
    output:
        DATA + "/vectors/numberbatch.h5"
    resources:
        ram=30
    shell:
        "cn5-vectors debias {input} {output}"

rule miniaturize:
    input:
        DATA + "/vectors/numberbatch-biased.h5",
        DATA + "/vectors/w2v-google-news.h5"
    output:
        DATA + "/vectors/mini.h5"
    resources:
        ram=4
    shell:
        "cn5-vectors miniaturize {input} {output}"

rule export_text:
    input:
        DATA + "/vectors/numberbatch.h5",
    output:
        DATA + "/vectors/plain/numberbatch.txt.gz"
    shell:
        "cn5-vectors export_text {input} {output}"


rule export_english_text:
    input:
        DATA + "/vectors/numberbatch.h5",
    output:
        DATA + "/vectors/plain/numberbatch-en.txt.gz"
    shell:
        "cn5-vectors export_text -l en {input} {output}"


# Morphology
# ==========

rule prepare_vocab:
    input:
        DATA + "/stats/core_concept_counts.txt"
    output:
        DATA + "/morph/vocab/{language}.txt"
    shell:
        "cn5-build prepare_morphology {wildcards.language} {input} {output}"

rule morfessor_segmentation:
    input:
        DATA + "/morph/vocab/{language}.txt"
    output:
        DATA + "/morph/segments/{language}.txt"
    run:
        if wildcards.language in ATOMIC_SPACE_LANGUAGES:
            shell("morfessor-train {input} -S {output} --traindata-list --nosplit-re '[^_].'")
        else:
            shell("morfessor-train {input} -S {output} -f '_' --traindata-list")

rule subwords:
    input:
        DATA + "/morph/segments/{language}.txt",
    output:
        DATA + "/edges/morphology/subwords-{language}.msgpack"
    shell:
        "cn5-build subwords {wildcards.language} {input} {output}"


# Evaluation
# ==========

rule compare_embeddings:
    input:
        DATA + "/raw/vectors/GoogleNews-vectors-negative300.bin.gz",
        DATA + "/raw/vectors/glove12.840B.300d.txt.gz",
        DATA + "/vectors/glove12-840B.h5",
        DATA + "/raw/vectors/fasttext-wiki-en.vec.gz",
        DATA + "/vectors/numberbatch-biased.h5",
        DATA + "/vectors/numberbatch.h5",
        DATA + "/raw/analogy/SAT-package-V3.txt",
        DATA + "/psql/done"
    output:
        DATA + "/stats/evaluation.h5"
    run:
        input_embeddings = input[:-2]
        input_embeddings_str = ' '.join(input_embeddings)
        shell("cn5-vectors compare_embeddings {input_embeddings_str} {output}")

rule comparison_graph:
    input:
        DATA + "/stats/evaluation.h5"
    output:
        DATA + "/stats/eval-graph.png"
    shell:
        "cn5-vectors comparison_graph {input} {output}"


ruleorder:
    join_retrofit > convert_polyglot

from snakemake.remote.HTTP import RemoteProvider as HTTPRemoteProvider
from conceptnet5.languages import COMMON_LANGUAGES, ATOMIC_SPACE_LANGUAGES

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

# If USE_MORPHOLOGY is true, we will build and learn from sub-words derived
# from Morfessor.
USE_MORPHOLOGY = False

# The versions of Wiktionary data to download. Updating these requires
# uploading new Wiktionary dumps to ConceptNet's S3.
WIKTIONARY_VERSIONS = {
    # English wiktionary formatting has gotten even harder to deal with, let's
    # stay with 2019 for now
    'en': '20190101',
    'fr': '20200301',
    'de': '20200301'
}
WIKTIONARY_LANGUAGES = sorted(list(WIKTIONARY_VERSIONS))

# Version of Unicode CLDR data, which will be downloaded separately from the
# ConceptNet raw data
CLDR_VERSION = '36.1'

# If it's a .0 release of CLDR, the .0 is be omitted from the directory name.
# For example, if the current version is '36.0', the short version should be
# '36'.
CLDR_VERSION_SHORT = '36.1'

# Languages where morphemes should not be split anywhere except at spaces
ATOMIC_SPACE_LANGUAGES = {'vi'}

# Languages that the CLDR emoji data is available in. These match the original
# filenames, not ConceptNet language codes; they are turned into ConceptNet
# language codes by the reader.
#
# This list is the list of languages with emoji names in CLDR v34.
EMOJI_LANGUAGES = [
    'af', 'am', 'ar', 'ar_SA', 'as', 'ast', 'az', 'be', 'bg', 'bn', 'br', 'bs', 'ca', 'ccp',
    'chr', 'cs', 'cy', 'da', 'de', 'de_CH', 'el', 'en', 'en_001', 'en_AU', 'en_CA', 'en_GB',
    'es', 'es_419', 'es_MX', 'es_US', 'et', 'eu', 'fa', 'fi', 'fil', 'fo', 'fr', 'fr_CA', 'ga',
    'gd', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy', 'ia', 'id', 'is', 'it', 'ja', 'ka', 'kab',
    'kk', 'km', 'kn', 'ko', 'ku', 'ky', 'lo', 'lt', 'lv', 'mk', 'ml', 'mn', 'mr', 'ms', 'my',
    'nb', 'ne', 'nl', 'nn', 'or', 'pa', 'pl', 'ps', 'pt', 'pt_PT', 'ro', 'ru', 'sd', 'si', 'sk',
    'sl', 'sq', 'sr', 'sr_Cyrl', 'sr_Cyrl_BA', 'sr_Latn', 'sr_Latn_BA', 'sv', 'sw', 'ta', 'te',
    'th', 'tk', 'to', 'tr', 'uk', 'ur', 'uz', 'vi', 'yue', 'yue_Hans', 'zh', 'zh_Hant',
    'zh_Hant_HK', 'zu'
]

# Increment this number when we incompatibly change the parser
WIKT_PARSER_VERSION = "3"

RETROFIT_SHARDS = 6
PROPAGATE_SHARDS = 6

# Dataset filenames
# =================
# The goal of reader steps is to produce Msgpack files, and later CSV files,
# with these names.
#
# We distingish *core dataset names*, which collectively determine the set of
# terms that ConceptNet will attempt to represent, from the additional datasets
# that will mainly be used to find more information about those terms.


RAW_DATA_URL = "https://zenodo.org/record/3739540/files/conceptnet-raw-data-5.8.zip"
PRECOMPUTED_DATA_PATH = "/precomputed-data/2016"
PRECOMPUTED_DATA_URL = "https://conceptnet.s3.amazonaws.com" + PRECOMPUTED_DATA_PATH
PRECOMPUTED_S3_UPLOAD = "s3://conceptnet" + PRECOMPUTED_DATA_PATH

# We need an external vocabulary to refer to when miniaturizing our set of
# embeddings. In the normal case, this is the word2vec Google News vocabulary.
# In the test build, we don't have that, we only have a cut-down version of GloVe,
# so we'll switch it to that instead.
MINI_VOCAB_SOURCE = "/vectors/w2v-google-news.h5"

INPUT_EMBEDDINGS = [
    'crawl-300d-2M', 'w2v-google-news', 'glove12-840B', 'fasttext-opensubtitles'
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

    DATA = "testdata/current"
    USE_PRECOMPUTED = True
    HASH_WIDTH = 12
    RAW_DATA_URL = "/missing/data"
    PRECOMPUTED_DATA_URL = "/missing/data"
    EMOJI_LANGUAGES = ['en', 'en_001']
    MINI_VOCAB_SOURCE = "/vectors/glove12-840B.h5"


CORE_DATASET_NAMES = [
    "jmdict/jmdict",
    "nadya/nadya",
    "ptt_petgame/api",
    "opencyc/opencyc",
    "verbosity/verbosity",
    "wordnet/wordnet",
    "cedict/cedict",
    "kyoto_yahoo/facts"
]
CORE_DATASET_NAMES += ["conceptnet4/conceptnet4_flat_{}".format(num) for num in range(10)]
CORE_DATASET_NAMES += ["ptt_petgame/part{}".format(num) for num in range(1, 13)]
CORE_DATASET_NAMES += ["wiktionary/{}".format(lang) for lang in WIKTIONARY_LANGUAGES]
CORE_DATASET_NAMES += ["emoji/{}".format(lang) for lang in EMOJI_LANGUAGES]


DATASET_NAMES = CORE_DATASET_NAMES + ["dbpedia/dbpedia_en"]
if USE_MORPHOLOGY:
    DATASET_NAMES += ["morphology/subwords-{}".format(lang) for lang in COMMON_LANGUAGES]


rule all:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_features.csv",
        DATA + "/psql/edges_gin.shuf.csv",
        DATA + "/psql/nodes.csv",
        DATA + "/psql/sources.csv",
        DATA + "/psql/relations.csv",
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
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_features.csv",
        DATA + "/psql/edges_gin.shuf.csv",
        DATA + "/psql/nodes.csv",
        DATA + "/psql/sources.csv",
        DATA + "/psql/relations.csv",
        DATA + "/psql/done",

rule clean:
    shell:
        "for subdir in assertions assoc collated db edges morph psql tmp vectors stats; "
        "do echo Removing {DATA}/$subdir; "
        "rm -rf {DATA}/$subdir; done"

rule test:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/psql/done",
        DATA + "/assoc/reduced.csv",
        DATA + "/vectors/mini.h5",
        DATA + "/vectors/plain/numberbatch-en.txt.gz",


# Downloaders
# ===========
rule download_raw_package:
    output:
        DATA + "/raw/conceptnet-raw-data-5.8.zip"
    shell:
        "wget -nv {RAW_DATA_URL} -O {output}"

# Get emoji data directly from Unicode CLDR
rule download_unicode_data:
    output:
        DATA + "/raw/cldr-common-" + CLDR_VERSION + ".zip"
    shell:
        "wget -nv https://conceptnet.s3.amazonaws.com/downloads/2020/cldr-common-{CLDR_VERSION}.zip -O {output}"

rule extract_raw:
    input:
        DATA + "/raw/conceptnet-raw-data-5.8.zip"
    output:
        DATA + "/raw/{dirname}/{filename}"
    shell:
        "unzip {input} raw/{wildcards.dirname}/{wildcards.filename} -d {DATA}"

# This rule takes precedence over extract_raw, extracting the emoji data from
# the Unicode CLDR zip file.
#
# TODO: integrate this with the rest of the raw data
rule extract_emoji_data:
    input:
        DATA + "/raw/cldr-common-" + CLDR_VERSION + ".zip"
    output:
        DATA + "/raw/emoji/{filename}"
    shell:
        # The -j option strips the path from the file we're extracting, so
        # we can use -d to put it in exactly the path we need.
        "unzip -j {input} common/annotations/{wildcards.filename} -d {DATA}/raw/emoji"


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
        DATA + "/raw/nadya/nadya-2017.csv",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/edges/nadya/nadya.msgpack"
    run:
        single_input = input[0]
        shell("cn5-read nadya {single_input} {output}")

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

rule read_kyoto_yahoo:
    input:
        DATA + "/raw/kyoto_yahoo/facts.tsv"
    output:
        DATA + "/edges/kyoto_yahoo/facts.msgpack"
    shell:
        "cn5-read kyoto_yahoo {input} {output}"


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

rule shuffle_edges:
    input:
        DATA + "/collated/sorted/edges.csv"
    output:
        DATA + "/collated/sorted/edges-shuf.csv"
    shell:
        "shuf {input} > {output}"

rule combine_assertions:
    input:
        DATA + "/collated/sorted/edges.csv",
        DATA + "/stats/core_concepts.txt"
    output:
        DATA + "/assertions/assertions.msgpack"
    shell:
        "cn5-build combine {input} {output}"


# Putting data in PostgreSQL
# ==========================
rule prepare_db:
    input:
        DATA + "/assertions/assertions.msgpack"
    output:
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_features.csv",
        temp(DATA + "/psql/edges_gin.csv"),
        DATA + "/psql/nodes.csv",
        DATA + "/psql/sources.csv",
        DATA + "/psql/relations.csv"
    shell:
        "cn5-db prepare_data {input} {DATA}/psql"

rule shuffle_gin:
    input:
        DATA + "/psql/edges_gin.csv"
    output:
        DATA + "/psql/edges_gin.shuf.csv"
    shell:
        "shuf {input} > {output}"

rule load_db:
    input:
        DATA + "/psql/edges.csv",
        DATA + "/psql/edge_features.csv",
        DATA + "/psql/edges_gin.shuf.csv",
        DATA + "/psql/nodes.csv",
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


rule concept_counts:
    input:
        DATA + "/stats/concepts_left.txt",
        DATA + "/stats/concepts_right.txt"
    output:
        DATA + "/stats/concept_counts.txt"
    shell:
        "cat {input} | grep '^/c/' | cut -d '/' -f 1,2,3,4 "
        "| LC_ALL=C sort | LC_ALL=C uniq -c > {output}"


rule core_concept_counts:
    input:
        DATA + "/stats/core_concepts_left.txt",
        DATA + "/stats/core_concepts_right.txt"
    output:
        DATA + "/stats/core_concept_counts.txt"
    shell:
        "cat {input} | grep '^/c/' | cut -d '/' -f 1,2,3,4 "
        "| LC_ALL=C sort | LC_ALL=C uniq -c > {output}"


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
        DATA + "/assoc/assoc.csv",
        expand(DATA + "/vectors/{name}.h5", name=INPUT_EMBEDDINGS)
    output:
        DATA + "/assoc/reduced.csv"
    shell:
        "cn5-build reduce_assoc {input} {output}"


# Building the vector space
# =========================
rule convert_word2vec:
    input:
        DATA + "/raw/vectors/GoogleNews-vectors-negative300.bin.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/w2v-google-news.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_word2vec -n {SOURCE_EMBEDDING_ROWS} {single_input} {output}")

rule convert_glove:
    input:
        DATA + "/raw/vectors/glove12.840B.300d.txt.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/glove12-840B.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_glove -n {SOURCE_EMBEDDING_ROWS} {single_input} {output}")

rule convert_fasttext_crawl:
    input:
        DATA + "/raw/vectors/crawl-300d-2M.vec.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/crawl-300d-2M.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {SOURCE_EMBEDDING_ROWS} {single_input} {output}")

rule convert_fasttext:
    input:
        DATA + "/raw/vectors/fasttext-wiki-{lang}.vec.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/fasttext-wiki-{lang}.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {SOURCE_EMBEDDING_ROWS} -l {wildcards.lang} {single_input} {output}")

rule convert_lexvec:
    input:
        DATA + "/raw/vectors/lexvec.commoncrawl.300d.W+C.pos.vectors.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/lexvec-commoncrawl.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {SOURCE_EMBEDDING_ROWS} {single_input} {output}")

rule convert_opensubtitles_ft:
    input:
        DATA + "/raw/vectors/ft-opensubtitles.vec.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/fasttext-opensubtitles.h5"
    resources:
        ram=24
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_fasttext -n {MULTILINGUAL_SOURCE_EMBEDDING_ROWS} {single_input} {output}")

rule convert_polyglot:
    input:
        DATA + "/raw/vectors/polyglot-{language}.pkl",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/polyglot-{language}.h5"
    run:
        single_input = input[0]
        shell("CONCEPTNET_DATA=data cn5-vectors convert_polyglot -l {wildcards.language} {single_input} {output}")

rule retrofit:
    input:
        DATA + "/vectors/{name}.h5",
        DATA + "/assoc/reduced.csv"
    output:
        temp(expand(DATA + "/vectors/{{name}}-retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS)))
    resources:
        ram=24
    shell:
        "cn5-vectors retrofit -n {RETROFIT_SHARDS} {input} {DATA}/vectors/{wildcards.name}-retrofit.h5"

rule join_retrofit:
    input:
        expand(DATA + "/vectors/{{name}}-retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS))
    output:
        DATA + "/vectors/{name}-retrofit.h5"
    resources:
        ram=24
    shell:
        "cn5-vectors join_shard_files -n {RETROFIT_SHARDS} {output}"

rule merge_intersect:
    input:
        expand(DATA + "/vectors/{name}-retrofit.h5", name=INPUT_EMBEDDINGS)
    output:
        DATA + "/vectors/numberbatch-retrofitted.h5",
        DATA + "/vectors/intersection-projection.h5"
    resources:
        ram=24
    shell:
        "cn5-vectors intersect {input} {output}"

rule propagate:
    input:
        DATA + "/assoc/assoc.csv",
        DATA + "/vectors/numberbatch-retrofitted.h5"
    output:
        temp(expand(DATA + "/vectors/numberbatch-biased.h5.shard{n}", n=range(PROPAGATE_SHARDS)))
    resources:
        ram=24
    shell:
        "cn5-vectors propagate -n {PROPAGATE_SHARDS} {input} {DATA}/vectors/numberbatch-biased.h5"

rule join_propagate:
    input:
        expand(DATA + "/vectors/numberbatch-biased.h5.shard{n}", n=range(PROPAGATE_SHARDS))
    output:
        DATA + "/vectors/numberbatch-biased.h5"
    resources:
        ram=24
    shell:
        "cn5-vectors join_shard_files -n {PROPAGATE_SHARDS} --sort {output}"

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
        DATA + MINI_VOCAB_SOURCE
    output:
        DATA + "/vectors/mini.h5"
    resources:
        ram=20
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
    join_retrofit > convert_polyglot > extract_emoji_data > extract_raw

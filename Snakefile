from snakemake.remote.HTTP import RemoteProvider as HTTPRemoteProvider
HTTP = HTTPRemoteProvider()

# Some build steps are difficult to run, so we've already run them and put
# the results in S3. Of course, that can't be the complete solution, because
# we have to have run those build steps first. So when USE_PRECOMPUTED is
# True, we will download the computed files; when it's False, we will compute
# them.
USE_PRECOMPUTED = False

# If USE_PRECOMPUTED is False, should we upload the files we compute so they
# can be used as precomputed files later? (Requires ConceptNet S3 credentials.)
UPLOAD = False

# How many pieces to split edge files into. (Works best when it's a power of
# 2 that's 64 or less.)
N_PIECES = 16

# ConceptNet is being indexed with a hash table that uses linear probing.
# Because of this, we want to keep the hash table about half full -- that is,
# keep about twice as much space for entries as actual entries.
#
# The `cn5-build-index` command will raise an error if the table is over
# 80% full, in which case you should increase this number, which will increase
# the size of the hash table.
#
# The index of the hash table will require 2 ^ (HASH_WIDTH + 4) bytes on disk,
# so a hash width of 27 takes up two gigabytes.
HASH_WIDTH = 27

# The versions of Wiktionary data to download. Updating these requires
# uploading new Wiktionary dumps to ConceptNet's S3.
WIKTIONARY_VERSIONS = {
    'en': '20160305',
    'fr': '20160305',
    'de': '20160407'
}
WIKTIONARY_LANGUAGES = sorted(list(WIKTIONARY_VERSIONS))

# Increment this number when we incompatibly change the parser
WIKT_PARSER_VERSION = "1"

# Dataset filenames
# =================
# The goal of reader steps is to produce Msgpack files, and later CSV files,
# with these names.

DATASET_NAMES = [
    "globalmind/globalmind",
    "jmdict/jmdict",
    "nadya/nadya",
    "ptt_petgame/api",
    "umbel/umbel",
    "umbel/umbel_links",
    "verbosity/verbosity",
    "wordnet/wordnet"
]
DATASET_NAMES += ["conceptnet4/conceptnet4_flat_{}".format(num) for num in range(10)]
DATASET_NAMES += ["ptt_petgame/part{}".format(num) for num in range(1, 13)]
DATASET_NAMES += ["wiktionary/{}".format(lang) for lang in WIKTIONARY_LANGUAGES]

RAW_DATA_URL = "conceptnet.s3.amazonaws.com/raw-data/2016"
PRECOMPUTED_DATA_PATH = "/precomputed-data/2016"
PRECOMPUTED_DATA_URL = "conceptnet.s3.amazonaws.com/precomputed-data/2016" + PRECOMPUTED_DATA_PATH
PRECOMPUTED_S3_UPLOAD = "s3://conceptnet" + PRECOMPUTED_DATA_PATH

rule all:
    input:
        "data/assertions/assertions.csv",
        "data/db/assertions.index",
        "data/stats/dataset_vs_language.txt",
        "data/stats/relations.txt",
        "data/assoc/reduced.csv"

# Downloaders
# ===========
rule download_raw:
    output:
        "data/raw/{dirname}/{filename}"
    shell:
        "curl {RAW_DATA_URL}/{wildcards.dirname}/{wildcards.filename} > {output}"


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
        filename = "data/raw/wiktionary/{0}wiktionary-{1}-pages-articles.xml.bz2".format(
            language, version
        )
        return [filename]

rule precompute_wiktionary:
    input:
        find_wiktionary_input
    output:
        "data/precomputed/wiktionary/parsed-{version}/{language}.jsons.gz"
    run:
        if USE_PRECOMPUTED:
            shell("curl {PRECOMPUTED_DATA_URL}/wiktionary/"
                  "parsed-{wildcards.version}/{wildcards.language}.jsons.gz "
                  "> {output}")
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
        "data/raw/conceptnet4/conceptnet4_flat_{num}.jsons"
    output:
        "data/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    shell:
        "python3 -m conceptnet5.readers.conceptnet4 {input} {output}"

rule read_globalmind:
    input:
        "data/raw/globalmind/frames.jsons",
        "data/raw/globalmind/users.jsons",
        "data/raw/globalmind/assertions.jsons",
        "data/raw/globalmind/translations.jsons"
    output:
        "data/edges/globalmind/globalmind.msgpack"
    shell:
        "python3 -m conceptnet5.readers.globalmind data/raw/globalmind {output}"

rule read_jmdict:
    input:
        "data/raw/jmdict/JMdict.xml"
    output:
        "data/edges/jmdict/jmdict.msgpack"
    shell:
        "python3 -m conceptnet5.readers.jmdict {input} {output}"

rule read_nadya:
    input:
        "data/raw/nadya/nadya-2014.csv"
    output:
        "data/edges/nadya/nadya.msgpack"
    shell:
        "python3 -m conceptnet5.readers.nadya {input} {output}"

rule read_ptt_petgame:
    input:
        "data/raw/ptt_petgame/conceptnet_zh_{part}.txt"
    output:
        "data/edges/ptt_petgame/{part}.msgpack"
    shell:
        "python3 -m conceptnet5.readers.ptt_petgame {input} {output}"

rule read_umbel:
    input:
        "data/raw/umbel/{filename}.nt"
    output:
        "data/edges/umbel/{filename}.msgpack",
        "data/edges/umbel/{filename}.links.csv"
    shell:
        "python3 -m conceptnet5.readers.umbel data/raw/umbel/ {output}"

rule read_verbosity:
    input:
        "data/raw/verbosity/verbosity.txt"
    output:
        "data/edges/verbosity/verbosity.msgpack"
    shell:
        "python3 -m conceptnet5.readers.verbosity {input} {output}"

rule prescan_wiktionary:
    input:
        expand(
            "data/precomputed/wiktionary/parsed-{version}/{language}.jsons.gz",
            version=[WIKT_PARSER_VERSION],
            language=WIKTIONARY_LANGUAGES
        )
    output:
        "data/db/wiktionary.db"
    shell:
        "mkdir -p data/tmp && "
        "cn5-read wiktionary_pre {input} data/tmp/wiktionary.db && "
        "mv data/tmp/wiktionary.db {output}"

rule read_wiktionary:
    input:
        "data/precomputed/wiktionary/parsed-%s/{language}.jsons.gz" % WIKT_PARSER_VERSION,
        "data/db/wiktionary.db"
    output:
        "data/edges/wiktionary/{language}.msgpack",
    shell:
        "cn5-read wiktionary {input} {output}"

rule read_wordnet:
    input:
        "data/raw/wordnet-rdf/wn31.nt"
    output:
        "data/edges/wordnet/wordnet.msgpack",
        "data/edges/wordnet/wordnet.links.csv"
    shell:
        "python3 -m conceptnet5.readers.wordnet {input} {output}"


# Converting msgpack to csv
# =========================

rule edge_msgpack_to_csv:
    input:
        "data/edges/{dir}/{filename}.msgpack"
    output:
        "data/edges/{dir,[^/]+}/{filename}.csv"
    shell:
        "python3 -m conceptnet5.builders.msgpack_to_csv {input} {output}"

rule assertion_msgpack_to_csv:
    input:
        "data/assertions/{filename}.msgpack"
    output:
        "data/assertions/{filename}.csv"
    shell:
        "python3 -m conceptnet5.builders.msgpack_to_csv {input} {output}"

rule collate_edges:
    input:
        expand("data/edges/{dataset}.csv", dataset=DATASET_NAMES)
    output:
        ["data/collated/unsorted/edges_{:02d}.csv".format(num)
         for num in range(N_PIECES)]
    shell:
        "python3 -m conceptnet5.builders.distribute_edges "
        "-o data/collated/unsorted/ -n {N_PIECES} {input}"

rule sort_edges:
    input:
        "data/collated/unsorted/{filename}.csv"
    output:
        "data/collated/sorted/{filename}.csv"
    shell:
        "LC_ALL=C sort {input} | uniq > {output}"

rule combine_assertions:
    input:
        ["data/collated/sorted/edges_{:02d}.csv".format(num)
         for num in range(N_PIECES)]
    output:
        "data/assertions/assertions.msgpack"
    shell:
        "python3 -m conceptnet5.builders.combine_assertions -o {output} {input}"

# Making an index file
# ====================
rule build_preindex:
    input:
        "data/assertions/assertions.msgpack"
    output:
        "data/db/assertions.preindex.txt"
    shell:
        "mkdir -p data/tmp "
        "&& python -m conceptnet5.builders.preindex_assertions {input} "
        "| LANG=C sort -T data/tmp "
        "| LANG=C uniq > {output}"

rule build_index:
    input:
        "data/db/assertions.preindex.txt"
    output:
        "data/db/assertions.index"
    shell:
        "cn5-build-index {input} {output} {HASH_WIDTH}"

# Collecting statistics
# =====================
rule relation_stats:
    input:
        "data/assertions/assertions.csv"
    output:
        "data/stats/relations.txt"
    shell:
        "cut -f 2 {input} | LC_ALL=C sort | LC_ALL=C uniq -c "
        "| LC_ALL=C sort -nbr > {output}"

rule dataset_stats_left:
    input:
        "data/assertions/assertions.csv"
    output:
        "data/stats/concepts_left_datasets.txt"
    shell:
        "cut -f 3,8 {input} > {output}"

rule dataset_stats_right:
    input:
        "data/assertions/assertions.csv"
    output:
        "data/stats/concepts_right_datasets.txt"
    shell:
        "cut -f 4,8 {input} > {output}"

rule dataset_vs_language:
    input:
        "data/stats/concepts_left_datasets.txt",
        "data/stats/concepts_right_datasets.txt"
    output:
        "data/stats/dataset_vs_language.txt"
    shell:
        "cat {input} | sed -r 's:((/[^/\t]+){{2}})[^\t]*:\\1:g' "
        "| LC_ALL=C sort | LC_ALL=C uniq -c > {output}"

# Building associations
# =====================
rule assertions_to_assoc:
    input:
        "data/assertions/assertions.msgpack"
    output:
        "data/assoc/assoc.csv"
    shell:
        "python3 -m conceptnet5.builders.msgpack_to_assoc {input} {output}"

rule reduce_assoc:
    input:
        "data/assoc/assoc.csv"
    output:
        "data/assoc/reduced.csv"
    shell:
        "python3 -m conceptnet5.builders.reduce_assoc {input} {output}"

# Building the vector space
# =========================
rule convert_word2vec:
    input:
        "data/raw/vectors/GoogleNews-vectors-negative300.bin.gz"
    output:
        "data/vectors/w2v-google-news.feather"
    shell:
        "cn5-vectors convert_word2vec {input} {output}"

rule convert_glove:
    input:
        "data/raw/vectors/glove12.840B.300d.txt.gz"
    output:
        "data/vectors/glove12.840B.feather"
    shell:
        "cn5-vectors convert_glove {input} {output}"

rule merge_interpolate:
    input:
        "data/vectors/glove12.840B.feather",
        "data/vectors/w2v-google-news.feather",
        "data/assoc/reduced.csv"
    output:
        "data/vectors/merged.feather"
    shell:
        "cn5-vectors interpolate -v -t 50000 {input} {output}"

rule retrofit:
    input:
        "data/vectors/merged.feather",
        "data/assoc/reduced.csv"
    output:
        "data/vectors/retrofit.feather"
    shell:
        "cn5-vectors retrofit -v {input} {output}"
from snakemake.remote.HTTP import RemoteProvider as HTTPRemoteProvider
import os
HTTP = HTTPRemoteProvider()

# The directory containing the data files. By default, this is "data" under
# the current directory, but it can be overridden using the
# CONCEPTNET_BUILD_DATA environment variable. This will happen during testing.
DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "data")

# If CONCEPTNET_BUILD_TEST is set, we're running the small test build.
TESTMODE = bool(os.environ.get("CONCEPTNET_BUILD_TEST"))

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

# ConceptNet is being indexed with a hash table that uses linear probing.
# Because of this, we want to keep the hash table about half full -- that is,
# keep about twice as much space for entries as actual entries.
#
# The `cn5-build-index` command will raise an error if the table is over
# 80% full, in which case you should increase this number, which will increase
# the size of the hash table.
#
# The index of the hash table will require 2 ^ (HASH_WIDTH + 4) bytes on disk,
# so a hash width of 28 takes up four gigabytes.
HASH_WIDTH = 28

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

RETROFIT_SHARDS = 6

# Dataset filenames
# =================
# The goal of reader steps is to produce Msgpack files, and later CSV files,
# with these names.
#
# We distingish *core dataset names*, which collectively determine the set of
# terms that ConceptNet will attempt to represent, from the additional datasets
# that will mainly be used to find more information about those terms.

CORE_DATASET_NAMES = [
    "jmdict/jmdict",
    "nadya/nadya",
    "ptt_petgame/api",
    "opencyc/opencyc",
    "verbosity/verbosity",
    "wordnet/wordnet"
]
CORE_DATASET_NAMES += ["conceptnet4/conceptnet4_flat_{}".format(num) for num in range(10)]
CORE_DATASET_NAMES += ["ptt_petgame/part{}".format(num) for num in range(1, 13)]
CORE_DATASET_NAMES += ["wiktionary/{}".format(lang) for lang in WIKTIONARY_LANGUAGES]

DATASET_NAMES = CORE_DATASET_NAMES + ["dbpedia/dbpedia_en"]

RAW_DATA_URL = "http://conceptnet.s3.amazonaws.com/raw-data/2016"
PRECOMPUTED_DATA_PATH = "/precomputed-data/2016"
PRECOMPUTED_DATA_URL = "http://conceptnet.s3.amazonaws.com" + PRECOMPUTED_DATA_PATH
PRECOMPUTED_S3_UPLOAD = "s3://conceptnet" + PRECOMPUTED_DATA_PATH


# Test mode overrides some of these settings.
if TESTMODE:
    DATA = "testdata"
    USE_PRECOMPUTED = True
    HASH_WIDTH = 12
    RAW_DATA_URL = "/missing/data"
    PRECOMPUTED_DATA_URL = "/missing/data"


rule all:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/index/assertions.index",
        DATA + "/stats/languages.txt",
        DATA + "/stats/relations.txt",
        DATA + "/assoc/reduced.csv",
        DATA + "/vectors/numberbatch.h5"

rule clean:
    shell:
        "for subdir in assertions collated db edges index tmp vectors stats; "
        "do echo Removing %(data)s/$subdir; "
        "rm -rf %(data)s/$subdir; done" % {'data': DATA}

rule test:
    input:
        DATA + "/assertions/assertions.csv",
        DATA + "/index/assertions.index",
        DATA + "/assoc/reduced.csv"

# Downloaders
# ===========
rule download_raw:
    output:
        DATA + "/raw/{dirname}/{filename}"
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
        DATA + "/raw/conceptnet4/conceptnet4_flat_{num}.jsons"
    output:
        DATA + "/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    shell:
        "python3 -m conceptnet5.readers.conceptnet4 {input} {output}"

rule read_dbpedia:
    input:
        DATA + "/raw/dbpedia/instance_types_en.tql.bz2",
        DATA + "/raw/dbpedia/interlanguage_links_en.tql.bz2",
        DATA + "/raw/dbpedia/mappingbased_objects_en.tql.bz2",
        DATA + "/stats/core_concepts.txt"
    output:
        DATA + "/edges/dbpedia/dbpedia_en.msgpack",
    shell:
        "python3 -m conceptnet5.readers.dbpedia %(data)s/raw/dbpedia "
        "{output} "
        "%(data)s/stats/core_concepts.txt " % {'data': DATA}

rule read_jmdict:
    input:
        DATA + "/raw/jmdict/JMdict.xml"
    output:
        DATA + "/edges/jmdict/jmdict.msgpack"
    shell:
        "python3 -m conceptnet5.readers.jmdict {input} {output}"

rule read_nadya:
    input:
        DATA + "/raw/nadya/nadya-2014.csv"
    output:
        DATA + "/edges/nadya/nadya.msgpack"
    shell:
        "python3 -m conceptnet5.readers.nadya {input} {output}"

rule read_ptt_petgame:
    input:
        DATA + "/raw/ptt_petgame/conceptnet_zh_{part}.txt"
    output:
        DATA + "/edges/ptt_petgame/{part}.msgpack"
    shell:
        "python3 -m conceptnet5.readers.ptt_petgame {input} {output}"

rule read_opencyc:
    input:
        DATA + "/raw/opencyc/opencyc-2012-05-10-readable.nq"
    output:
        DATA + "/edges/opencyc/opencyc.msgpack"
    shell:
        "python3 -m conceptnet5.readers.opencyc {input} {output}"

rule read_verbosity:
    input:
        DATA + "/raw/verbosity/verbosity.txt"
    output:
        DATA + "/edges/verbosity/verbosity.msgpack"
    shell:
        "python3 -m conceptnet5.readers.verbosity {input} {output}"

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
        "mkdir -p %(data)s/tmp && "
        "cn5-read wiktionary_pre {input} %(data)s/tmp/wiktionary.db && "
        "mv %(data)s/tmp/wiktionary.db {output}" % {'data': DATA}

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
        "python3 -m conceptnet5.readers.wordnet {input} {output}"


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

rule distribute_edges:
    input:
        expand(DATA + "/edges/{dataset}.csv", dataset=DATASET_NAMES)
    output:
        [DATA + "/collated/unsorted/edges_{:02d}.csv".format(num)
         for num in range(N_PIECES)]
    shell:
        "python3 -m conceptnet5.builders.distribute_edges "
        "-o %s/collated/unsorted/ -n {N_PIECES} {input}" % DATA

rule sort_edges:
    input:
        DATA + "/collated/unsorted/{filename}.csv"
    output:
        DATA + "/collated/sorted/{filename}.csv"
    shell:
        "LC_ALL=C sort {input} | uniq > {output}"

rule combine_assertions:
    input:
        [DATA + "/collated/sorted/edges_{:02d}.csv".format(num)
         for num in range(N_PIECES)]
    output:
        DATA + "/assertions/assertions.msgpack"
    shell:
        "python3 -m conceptnet5.builders.combine_assertions -o {output} {input}"

# Making an index file
# ====================
rule build_assertion_preindex:
    input:
        DATA + "/assertions/assertions.msgpack"
    output:
        DATA + "/index/assertions.preindex.txt"
    shell:
        "mkdir -p %(data)s/tmp "
        "&& python -m conceptnet5.builders.preindex_assertions {input} "
        "| LANG=C sort -T %(data)s/tmp "
        "| LANG=C uniq > {output}" % {'data': DATA}


rule build_index:
    input:
        DATA + "/index/{name}.preindex.txt"
    output:
        DATA + "/index/{name}.index"
    shell:
        "cn5-build-index {input} {output} {HASH_WIDTH}"

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
        DATA + "/raw/vectors/GoogleNews-vectors-negative300.bin.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/w2v-google-news.h5"
    resources:
        ram=16
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_word2vec -n 1500000 data/raw/vectors/GoogleNews-vectors-negative300.bin.gz {output}"

rule convert_glove:
    input:
        DATA + "/raw/vectors/glove12.840B.300d.txt.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/glove12.840B.h5"
    resources:
        ram=16
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_glove -n 1500000 data/raw/vectors/glove12.840B.300d.txt.gz {output}"

rule convert_lexvec:
    input:
        DATA + "/raw/vectors/lexvec.no-header.vectors.gz",
        DATA + "/db/wiktionary.db"
    output:
        DATA + "/vectors/lexvec.h5"
    resources:
        ram=16
    shell:
        "CONCEPTNET_DATA=data cn5-vectors convert_glove -n 1500000 data/raw/vectors/lexvec.no-header.vectors.gz {output}"

rule merge_interpolate:
    input:
        DATA + "/vectors/glove12.840B.h5",
        DATA + "/vectors/w2v-google-news.h5",
        DATA + "/assoc/reduced.csv"
    output:
        DATA + "/vectors/merged.h5"
    resources:
        ram=16
    shell:
        "CONCEPTNET_DATA=data cn5-vectors interpolate -v -t 50000 {input} {output}"

rule retrofit:
    input:
        DATA + "/vectors/merged.h5",
        DATA + "/assoc/reduced.csv"
    output:
        expand(DATA + "/vectors/retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS))
    resources:
        ram=16
    shell:
        "cn5-vectors retrofit -s {RETROFIT_SHARDS} -v {input} data/vectors/retrofit.h5"

rule shrink_embeddings:
    input:
        DATA + "/vectors/retrofit.h5"
    output:
        DATA + "/vectors/numberbatch.h5"
    shell:
        "cn5-vectors shrink {input} {output} -n 1000000 -k 300"

rule join_retrofit:
    input:
        expand(DATA + "/vectors/retrofit.h5.shard{n}", n=range(RETROFIT_SHARDS))
    output:
        DATA + "/vectors/retrofit.h5"
    resources:
        ram=16
    shell:
        "cn5-vectors join_retrofit -s {RETROFIT_SHARDS} {output}"

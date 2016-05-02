from snakemake.remote.HTTP import RemoteProvider as HTTPRemoteProvider
HTTP = HTTPRemoteProvider()

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
# so a hash width of 26 takes up half a gigabyte.
HASH_WIDTH = 26

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

RAW_DATA_URL = "conceptnet.s3.amazonaws.com/raw-data"

# Downloaders
# ===========
rule download_raw:
    input:
        HTTP.remote(RAW_DATA_URL + '/2016/{dirname,[^/]+}/{filename}')
    output:
        "data/raw/conceptnet4/{filename}"

# Readers
# =======
# These are steps that turn raw data into files of uncombined 'edges'.

rule all:
    input:
        "data/assertions/assertions.csv",
        "data/db/assertions.index",
        "data/stats/dataset_vs_language.txt",
        "data/stats/relations.txt"

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
        "data/edges/umbel/{filename}.links.jsons"
    shell:
        "python3 -m conceptnet5.readers.umbel data/raw/umbel/ {output}"

rule read_verbosity:
    input:
        "data/raw/verbosity/verbosity.txt"
    output:
        "data/edges/verbosity/verbosity.msgpack"
    shell:
        "python3 -m conceptnet5.readers.verbosity {input} {output}"

rule read_wordnet:
    input:
        "data/raw/wordnet-rdf/wn31.nt"
    output:
        "data/edges/wordnet/wordnet.msgpack",
        "data/edges/wordnet/wordnet.links.jsons"
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
        "cut -f 3,9 {input} > {output}"

rule dataset_stats_right:
    input:
        "data/assertions/assertions.csv"
    output:
        "data/stats/concepts_right_datasets.txt"
    shell:
        "cut -f 4,9 {input} > {output}"

rule dataset_vs_language:
    input:
        "data/stats/concepts_left_datasets.txt",
        "data/stats/concepts_right_datasets.txt"
    output:
        "data/stats/dataset_vs_language.txt"
    shell:
        "cat {input} | sed -r 's:((/[^/\t]+){{2}})[^\t]*:\\1:g' "
        "| LC_ALL=C sort | LC_ALL=C uniq -c > {output}"

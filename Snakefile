# How many pieces to split edge files into. (Works best when it's a power of
# 2 that's 64 or less.)
N_PIECES = 16

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


# Readers
# =======
# These are steps that turn raw data into files of uncombined 'edges'.

rule all:
    input: "data/assertions/assertions.csv"

rule read_conceptnet4:
    input:
        "data/raw/conceptnet4/conceptnet4_flat_{num}.jsons"
    output:
        "data/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    shell:
        "python3 -m conceptnet5.readers.conceptnet4 {input} {output}"

rule read_globalmind:
    input:
        "data/raw/globalmind/GMFrame.yaml",
        "data/raw/globalmind/GMTranslation.yaml",
        "data/raw/globalmind/GMAssertion.yaml",
        "data/raw/globalmind/GMUser.yaml"
    output: "data/edges/globalmind/globalmind.msgpack"
    shell: "python3 -m conceptnet5.readers.globalmind data/raw/globalmind {output}"

rule read_jmdict:
    input: "data/raw/jmdict/JMdict.xml"
    output: "data/edges/jmdict/jmdict.msgpack"
    shell: "python3 -m conceptnet5.readers.jmdict {input} {output}"

rule read_nadya:
    input: "data/raw/nadya/nadya-2014.csv"
    output: "data/edges/nadya/nadya.msgpack"
    shell: "python3 -m conceptnet5.readers.nadya {input} {output}"

rule read_ptt_petgame:
    input: "data/raw/conceptnet_zh/conceptnet_zh_{part}.txt"
    output: "data/edges/ptt_petgame/{part}.msgpack"
    shell: "python3 -m conceptnet5.readers.ptt_petgame {input} {output}"

rule read_umbel:
    input: "data/raw/umbel/{filename}.nt"
    output:
        "data/edges/umbel/{filename}.msgpack",
        "data/edges/umbel/{filename}.links.jsons"
    shell: "python3 -m conceptnet5.readers.umbel data/raw/umbel/ {output}"

rule read_verbosity:
    input: "data/raw/verbosity/verbosity.txt"
    output: "data/edges/verbosity/verbosity.msgpack"
    shell: "python3 -m conceptnet5.readers.verbosity {input} {output}"

rule read_wordnet:
    input: "data/raw/wordnet-rdf/wn31.nt"
    output:
        "data/edges/wordnet/wordnet.msgpack",
        "data/edges/wordnet/wordnet.links.jsons"
    shell: "python3 -m conceptnet5.readers.wordnet {input} {output}"

# Converting msgpack to csv
# =========================

rule edge_msgpack_to_csv:
    input: "data/edges/{dir}/{filename}.msgpack"
    output: "data/edges/{dir,[^/]+}/{filename}.csv"
    shell: "python3 -m conceptnet5.builders.msgpack_to_csv {input} {output}"

rule assertion_msgpack_to_csv:
    input: "data/assertions/{filename}.msgpack"
    output: "data/assertions/{filename}.csv"
    shell: "python3 -m conceptnet5.builders.msgpack_to_csv {input} {output}"

rule collate_edges:
    input: expand("data/edges/{dataset}.csv", dataset=DATASET_NAMES)
    output: ["data/collated/unsorted/edges_{:02d}.csv".format(num) for num in range(N_PIECES)]
    shell: "python3 -m conceptnet5.builders.distribute_edges -o data/collated/unsorted/ -n {N_PIECES} {input}"

rule sort_edges:
    input: "data/collated/unsorted/{filename}.csv"
    output: "data/collated/sorted/{filename}.csv"
    shell: "LC_ALL=C sort {input} | uniq > {output}"

rule combine_assertions:
    input: ["data/collated/sorted/edges_{:02d}.csv".format(num) for num in range(N_PIECES)]
    output: "data/assertions/assertions.msgpack"     
    shell: "python3 -m conceptnet5.builders.combine_assertions -o {output} {input}"
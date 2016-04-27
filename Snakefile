rule read_conceptnet4:
    input:
        "data/raw/conceptnet4/conceptnet4_flat_{num}.jsons"
    output:
        "data/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    shell:
        "python -m conceptnet5.readers.conceptnet4 {input} {output}"

rule read_wordnet:
    input:
        "data/raw/wordnet-rdf/wn31.nt"
    output:
        "data/edges/wordnet/wordnet.msgpack",
        "data/edges/wordnet/wordnet.sw_map.jsons"
    shell:
        "python -m conceptnet5.readers.wordnet {input} {output}"
    
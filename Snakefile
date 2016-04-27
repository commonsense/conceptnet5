rule read_conceptnet4:
    input:
        "data/raw/conceptnet4/conceptnet4_flat_{num}.jsons"
    output:
        "data/edges/conceptnet4/conceptnet4_flat_{num}.msgpack"
    shell:
        "python -m conceptnet5.readers.conceptnet4 {input} {output}"

rule read_wordnet:
    input: "data/raw/wordnet-rdf/wn31.nt"
    output:
        "data/edges/wordnet/wordnet.msgpack",
        "data/edges/wordnet/wordnet.links.jsons"
    shell: "python -m conceptnet5.readers.wordnet {input} {output}"

rule read_umbel:
    input: "data/raw/umbel/{filename}.nt"
    output:
        "data/edges/umbel/{filename}.msgpack",
        "data/edges/umbel/{filename}.links.jsons"
    shell: "python -m conceptnet5.readers.umbel {input} {output}"

rule read_jmdict:
    input: "data/raw/jmdict/JMDict.xml"
    output: "data/edges/jmdict/jmdict.msgpack"
    shell: "python


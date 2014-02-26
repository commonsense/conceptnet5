from __future__ import unicode_literals, print_function
import xmltodict
import re
import json
import codecs
from conceptnet5.util.language_codes import CODE_TO_ENGLISH_NAME, ENGLISH_NAME_TO_CODE
from conceptnet5.json_stream import JSONStreamWriter
from conceptnet5.uri import concept_uri, Licenses
from conceptnet5.edges import make_edge

# I took the time to record these, but in the end I don't think I plan
# to use them. Japanese parts of speech don't fit neatly into
# ConceptNet's neat n/v/a/r types.
#
# The idea was to record the parts of speech by the first 10 characters
# of their category in JMdict (because they're automatically decoded
# from their more helpful entity form).
NOUN_TYPES = [
    "nouns whic",
    "noun (comm",
    "adverbial ",
    "noun, used",
    "noun (temp",
    "noun or pa",
]
ADJ_TYPES = [
    "adjective ",
    "adjectival",
    "pre-noun a",
]
ADV_TYPES = [
    "adverb (fu",
    "adverb tak",
]
VERB_TYPES = [
    "Ichidan ve",
    "Nidan verb",
    "Yodan verb",
    "Godan verb",
    "intransiti",
    "Kuru verb ",
    "irregular ",
    "su verb - ",
    "suru verb ",
]


def convert_lang_code(code):
    """
    Map a language code to the canonical one that ConceptNet 5 uses,
    which is either the alpha2 code, or the "terminology" alpha3 code if no
    alpha2 code exists
    
    JMdict uses the "bibliographic" alpha3 code, which is often equal to
    neither of these, but we can map it to a canonical one by running it back
    and forth through our language name dictionaries.
    """
    return ENGLISH_NAME_TO_CODE[CODE_TO_ENGLISH_NAME[code]]


def get_list(node, tag):
    """
    Get sub-nodes of this node by their tag, and make sure to return a list,
    even if there's only one result.
    """
    subnode = node.get(tag, [])
    if isinstance(subnode, list):
        return subnode
    else:
        return [subnode]


def get_one(node, tag):
    """
    Get one sub-node of this node by its tag. If there are none, return None.
    """
    subnode = node.get(tag, None)
    if isinstance(subnode, list):
        return subnode[0]
    else:
        return subnode


GLOSS_RE = re.compile(r'''
    # Separate out text in parentheses or brackets.
    ^
    (\(.*?\)|\[.*?\] )?   # possibly a bracketed expression before the gloss
    (.*?)                 # the gloss itself
    ( \(.*?\)|\[.*?\])?   # possibly a bracketed expression after the gloss
    $
''', re.VERBOSE)
def parse_gloss(text):
    matched = GLOSS_RE.match(text)
    if matched:
        return matched.group(2).strip()
    else:
        return None


# TODO: write comments and a docstring.
def read_jmdict(filename, outfilename):
    file = codecs.open(filename, encoding='utf-8')
    out = JSONStreamWriter(outfilename)
    data = file.read()
    file.close()

    xml = xmltodict.parse(data)
    entries = xml['JMdict']['entry']
    for entry in entries:
        headwords = [word['keb'] for word in get_list(entry, 'k_ele')]
        if not headwords:
            headwords = [word['reb'] for word in get_list(entry, 'r_ele')]
        
        for sense in get_list(entry, 'sense'):
            glosses = get_list(sense, 'gloss') + get_list(sense, 'lsource')
            for gloss in glosses:
                if '#text' in gloss:
                    text = parse_gloss(gloss['#text'])
                    if '.' not in text:
                        lang = convert_lang_code(gloss['@xml:lang'])
                        for head in headwords:
                            ja_concept = concept_uri('ja', head)
                            other_concept = concept_uri(lang, text)
                            if len(other_concept.split('_')) <= 5:
                                output_edge(out, ja_concept, other_concept)
    out.close()


def output_edge(out, subj_concept, obj_concept):
    """
    Write an edge to `out`, an instance of JSONFileWriter.
    """
    rel = '/r/TranslationOf'
    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/jmdict',
                     license=Licenses.cc_sharealike,
                     sources=['/s/jmdict/1.07'],
                     weight=0.5)
    out.write(edge)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='XML copy of JMDict to read')
    parser.add_argument('output', help='JSON-stream file to output to')
    args = parser.parse_args()
    read_jmdict(args.input, args.output)


if __name__ == '__main__':
    main()

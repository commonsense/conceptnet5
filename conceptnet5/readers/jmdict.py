import xmltodict
import sys
import re
import codecs
import pycountry
from conceptnet5.nodes import make_concept_uri

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
    language = pycountry.languages.get(bibliographic=code)
    try:
        short_code = language.alpha2
    except AttributeError:
        short_code = language.terminology
    return short_code

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

def read_jmdict(filename, outfilename):
    file = open(filename)
    outfile = codecs.open(outfilename, 'w', encoding='utf-8')
    data = file.read().decode('utf-8')
    file.close()

    xml = xmltodict.parse(data)
    entries = xml['JMdict']['entry']
    for entry in entries:
        headwords = [word['keb'] for word in get_list(entry, 'k_ele')]
        if not headwords:
            headwords = [word['reb'] for word in get_list(entry, 'r_ele')]
        
        for sense in get_list(entry, 'sense'):
            pos = get_one(sense, 'pos')
            glosses = get_list(sense, 'gloss') + get_list(sense, 'lsource')
            for gloss in glosses:
                if '#text' in gloss:
                    text = parse_gloss(gloss['#text'])
                    if '.' not in text:
                        lang = convert_lang_code(gloss['@xml:lang'])
                        for head in headwords:
                            ja_concept = make_concept_uri(head, 'ja')
                            other_concept = make_concept_uri(text, lang)
                            if len(other_concept.split('_')) <= 5:
                                output_edge(outfile, ja_concept, other_concept)
    outfile.close()

def output_edge(outfile, subj_concept, obj_concept):
    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/jmdict',
                     license='/l/CC/By-SA',
                     sources=['/s/jmdict/1.07'],
                     context='/ctx/all',
                     weight=0.5)
    print >> outfile, json.dumps(obj, ensure_ascii=False)

if __name__ == '__main__':
    read_jmdict(sys.argv[1], sys.argv[2])

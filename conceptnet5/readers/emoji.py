import xml.etree.ElementTree as ET

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import Licenses

REL = '/r/SymbolOf'
DATASET = '/d/emoji'
LICENSE = Licenses.cc_attribution
SOURCE = [{'contributor': '/s/resource/unicode/cldr/32.0.1'}]


def strip_words(text):
    """
    When multiple words (separated by '|') are
    used to describe emojis, we need to remove the
    '|' in order to create edges for each word.
    This function takes out the '|' and puts all
    the words into a list.
    """
    return text.split(' | ')


def handle_file(input_file, output_file):
    tree = ET.parse(input_file)
    out = MsgpackStreamWriter(output_file)
    root = tree.getroot()
    lang = root[0][1].attrib[
        'type'
    ]  # language is at position [1] within the child node [0]

    if len(root) >= 2:
        for annotation in root[1]:
            for word in strip_words(annotation.text):
                start = standardized_concept_uri('mul', annotation.attrib['cp'])
                end = standardized_concept_uri(lang, word)
                edge = make_edge(REL, start, end, DATASET, LICENSE, SOURCE)
                out.write(edge)
    else:
        print("No emoji data in {!r}".format(input_file))

    out.close()

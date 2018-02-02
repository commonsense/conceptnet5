from collections import defaultdict

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.languages import ATOMIC_SPACE_LANGUAGES
from conceptnet5.nodes import get_uri_language, split_uri
from conceptnet5.uri import Licenses, join_uri


def prepare_vocab_for_morphology(language, input, output):
    vocab_counts = defaultdict(int)
    for line in input:
        countstr, uri = line.strip().split(' ', 1)
        if get_uri_language(uri) == language:
            term = split_uri(uri)[2]
            if language in ATOMIC_SPACE_LANGUAGES:
                term += '_'
            vocab_counts[term] += int(countstr)

    for term, count in sorted(list(vocab_counts.items())):
        print(count, term, file=output)


MORPH_SOURCES = [{'process': '/s/rule/morfessor'}]


def subwords_to_edges(language, input, output):
    """
    Morfessor hypothesizes ways to break words into sub-word chunks. Produce
    edges from these sub-words that can be used in retrofitting.
    """
    writer = MsgpackStreamWriter(output)
    for line in input:
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue

        # Remove the unnecessary count ("1 ") from the start of each line
        line = line.split(' ', 1)[1]
        chunks = line.split(' + ')

        # Strip a possible trailing underscore, which would particularly show
        # up in the way we segment ATOMIC_SPACE_LANGUAGES (Vietnamese)
        full_text = ''.join(chunks).strip('_')
        end = join_uri('c', language, full_text)
        for chunk in chunks:
            if chunk != '_':
                start = join_uri('x', language, chunk.strip('_'))
                edge = make_edge(
                    '/r/SubwordOf', start, end,
                    dataset='/d/morphology',
                    license=Licenses.cc_attribution,
                    sources=MORPH_SOURCES,
                    weight=0.01
                )
                writer.write(edge)
    writer.close()

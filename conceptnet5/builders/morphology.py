from collections import defaultdict

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.languages import ATOMIC_SPACE_LANGUAGES
from conceptnet5.nodes import split_uri
from conceptnet5.uri import Licenses, get_uri_language, join_uri


def prepare_vocab_for_morphology(language, input, output):
    """
    Morfessor's input is a list of terms with their counts. Here, we
    read a ConceptNet vocabulary file with counts (core_concept_counts.txt),
    filter it for a single language, and convert it into the input form that
    Morfessor expects.

    We're stripping out the word sense information here, which would cause
    the same term to appear multiple times. Because of that, we build up
    a new dictionary of counts, summing all occurrences of a term.

    We use _ to represent all spaces. In languages where the space-separated
    segments are atomic (Vietnamese), we use _ to represent the locations where
    subwords are allowed to end, and thus add _ to the end of the term as well.
    """
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
                    '/r/SubwordOf',
                    start,
                    end,
                    dataset='/d/morphology',
                    license=Licenses.cc_attribution,
                    sources=MORPH_SOURCES,
                    weight=0.01,
                )
                writer.write(edge)
    writer.close()

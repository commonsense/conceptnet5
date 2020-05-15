import itertools
import json
import os

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.languages import ALL_LANGUAGES
from conceptnet5.readers.wiktionary import valid_language
from conceptnet5.uri import (
    Licenses,
    conjunction_uri,
    get_uri_language,
    is_absolute_url,
    split_uri,
    uri_prefix,
    uri_prefixes,
)
from conceptnet5.util import get_support_data_filename

N = 100
CURRENT_DIR = os.getcwd()


if os.environ.get('CONCEPTNET_BUILD_TEST'):
    BLOCK_FILENAME = 'fake_blocklist.txt'
else:
    BLOCK_FILENAME = 'blocklist.txt'


class Blocklist:
    """
    A class that keeps track of what node values we want to exclude from ConceptNet.
    It can be loaded from a text file (see `support_data/blocklist.txt`, or the tame
    version, `support_data/fake_blocklist.txt`).

    "Simple blocks" are the URIs that appear on lines by themselves in the blocklist
    file. If this URI is any of the values in an edge's dictionary -- such as its
    start, end, or complete assertion URI -- the edge will be blocked.

    "Derivation blocks" make use of the structure of DerivedFrom edges that we
    get from Wiktionary. Any word DerivedFrom a concept that is listed as a
    derivation block will be added as a "simple block" _and_ a "derivation
    block". This allows us to block many forms of the same word, even though
    the derived word forms might not have the same warnings as the root word.

    This means that the words that get blocked depend on the order of the edges
    that come from Wiktionary. The edges are ordered the same as the Wiktionary
    DB dump, which is ordered by when the page was created. Often, derived
    forms of words are created after the page for the root word, but there are
    enough exceptions to this that we have to run propagation twice.

    A word that is a derivation block is not necessarily a simple block. A case
    exists where one sense of a word is a racial slur, while its other senses
    are benign. Because we can't tell what word sense is being derived, we
    block all its derived terms (many of which are slurs). But we allow the
    non-slur meanings of the root word.
    """

    def __init__(self):
        self.simple_blocks = set()
        self.derivation_blocks = set()

    @staticmethod
    def load(filename):
        """
        Load the blocklist from a file.

        Empty lines and lines starting with the comment symbol '#' are ignored.
        Lines that start with 'DERIVED ' are derivation blocks. All other lines
        are simple blocks.
        """
        bl = Blocklist()
        for line in open(filename):
            entry = line.strip()
            if entry and not entry.startswith('#'):
                if entry.upper().startswith('DERIVED '):
                    entry = entry[8:]
                    bl.derivation_blocks.add(entry)
                else:
                    bl.simple_blocks.add(entry)
        return bl

    def propagate_blocks(self, edge, verbose=False):
        """
        Scan an edge and see if it is a DerivedFrom or FormOf edge whose right
        side matches a derivation block. If so, add its left side as a simple
        block and a derivation block.
        """
        if edge['rel'].endswith('DerivedFrom') or edge['rel'].endswith('FormOf'):
            if set(uri_prefixes(edge['end'])) & self.derivation_blocks:
                prefix = uri_prefix(edge['start'], 3)
                self.simple_blocks.add(prefix)
                self.derivation_blocks.add(prefix)
                if verbose:
                    print(f"Added derivation block: {prefix}")

    def is_blocked(self, edge):
        """
        Test whether an edge should be blocked (whether any of its string values
        match a simple block).
        """
        edge_values = set(
            [
                prefix
                for value in edge.values()
                if isinstance(value, str)
                for prefix in uri_prefixes(value)
            ]
        )
        return bool(edge_values & self.simple_blocks)


def weight_scale(weight):
    """
    This scale starts out linear, then switches to a square-root scale at x=2.

    >>> weight_scale(-1)
    -1.0
    >>> weight_scale(0)
    0.0
    >>> weight_scale(1)
    1.0
    >>> weight_scale(2)
    2.0
    >>> weight_scale(5)
    4.0
    >>> weight_scale(10)
    6.0
    """
    return 2 * max(weight - 1, 1) ** .5 + min(weight, 2) - 2


def keep_concept(uri):
    # FIXME: possibly we should use the 'is_valid_concept' check that we use
    # elsewhere
    if is_absolute_url(uri):
        return True
    if get_uri_language(uri) not in ALL_LANGUAGES:
        return False
    if not valid_language(get_uri_language(uri)):
        return False
    pieces = split_uri(uri)
    return bool(pieces[2])


def _make_assertion(line_group):
    """
    When a generator of tab-separated lines has been grouped by their assertion
    URI, this function takes all the lines with the same URI and makes a single
    assertion out of them.
    """
    lines = [line.rstrip() for line in line_group]
    lines = [line for line in lines if line]
    if not lines:
        return None

    # FIXME: the steps leading up to this produce URIs that can differ based
    # on word senses. These don't get merged together, but they should.
    uri, rel, start, end, _ = lines[0].split('\t')

    if not (keep_concept(start) and keep_concept(end)):
        return None

    info_dicts = [json.loads(line.split('\t')[4]) for line in lines]
    unscaled_weight = sum(info['weight'] for info in info_dicts)
    licenses = {info['license'] for info in info_dicts}
    dataset = info_dicts[0]['dataset']
    surface_text = None
    sources = []
    seen_sources = set()
    for info in info_dicts:
        if surface_text is None and 'surfaceText' in info:
            surface_text = info['surfaceText']
        for subsource in info['sources']:
            conjunction = conjunction_uri(*sorted(subsource.values()))
            if conjunction not in seen_sources:
                sources.append(subsource)
                seen_sources.add(conjunction)

    weight = weight_scale(unscaled_weight)
    if Licenses.cc_sharealike in licenses:
        license = Licenses.cc_sharealike
    else:
        license = Licenses.cc_attribution

    return make_edge(
        rel=rel,
        start=start,
        end=end,
        weight=weight,
        dataset=dataset,
        license=license,
        sources=sources,
        surfaceText=surface_text,
    )


def combine_assertions(input_filename, core_filename, output_filename):
    """
    Take in a tab-separated, sorted "CSV" files, indicated by
    `input_filename`, that should be grouped together into assertions.
    Output a msgpack stream of assertions the file indicated by
    `output_filename`.

    The input file should be made from multiple sources of assertions by
    concatenating and sorting them.

    The combined assertions will all have the dataset of the first edge that
    produces them, and the license of the strongest license being combined.

    This process requires its input to be a sorted CSV so that all edges for
    the same assertion will appear consecutively.
    """

    def group_func(line):
        "Group lines by their URI (their first column)."
        return line.split('\t', 1)[0]

    out = MsgpackStreamWriter(output_filename)
    out_bad = MsgpackStreamWriter(output_filename + '.reject')

    core_prefixes = set()
    for line in open(core_filename, encoding='utf-8'):
        core_prefixes.add(uri_prefix(line.strip(), 3))

    # Scan through the assertions twice to add derived words to the blocklist
    blocklist = Blocklist.load(get_support_data_filename(BLOCK_FILENAME))
    for iter in range(2):
        with open(input_filename, encoding='utf-8') as stream:
            for line in stream:
                tmp_assertion = _make_assertion([line.strip()])
                if tmp_assertion is None:
                    continue
                blocklist.propagate_blocks(tmp_assertion)

    with open(input_filename, encoding='utf-8') as stream:
        for key, line_group in itertools.groupby(stream, group_func):
            assertion = _make_assertion(line_group)
            destination = out
            if assertion is None:
                continue
            if assertion['weight'] <= 0:
                destination = out_bad
            if blocklist.is_blocked(assertion):
                destination = out_bad
            if assertion['rel'] == 'ExternalURL':
                # discard ExternalURL edges for things that aren't otherwise
                # in ConceptNet
                prefix = uri_prefix(assertion['start'], 3)
                if prefix not in core_prefixes:
                    destination = out_bad
            destination.write(assertion)

    out.close()
    out_bad.close()

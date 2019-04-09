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
)
from conceptnet5.util import get_support_data_filename

N = 100
CURRENT_DIR = os.getcwd()


def get_blacklist():
    filename = get_support_data_filename('blacklist.txt')
    return set(open(filename).readlines())


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


def make_assertion(line_group):
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


def combine_assertions(input_filename, output_filename):
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

    blacklist = get_blacklist()

    with open(input_filename, encoding='utf-8') as stream:
        for key, line_group in itertools.groupby(stream, group_func):
            assertion = make_assertion(line_group)
            destination = out
            if assertion is None:
                continue
            if assertion['weight'] <= 0:
                destination = out_bad
            for value in assertion.values():
                if isinstance(value, str) and value in blacklist:
                    destination = out_bad
            destination.write(assertion)

    out.close()
    out_bad.close()

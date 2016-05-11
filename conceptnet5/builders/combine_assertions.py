from __future__ import unicode_literals, print_function
from conceptnet5.nodes import ALL_LANGUAGES, get_uri_language
from conceptnet5.edges import make_edge
from conceptnet5.uri import disjunction_uri, parse_compound_uri, Licenses
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.util import get_support_data_filename
import os

N = 100
CURRENT_DIR = os.getcwd()


def weight_scale(weight):
    """
    This scale starts out linear, then switches to a square-root scale at x=2.
    """
    return 2 * max(weight - 1, 1) ** .5 + min(weight, 2) - 2


def read_reliability_file(filename):
    reliability = {}
    for line in open(filename, encoding='utf-8'):
        line = line.rstrip()
        if line:
            score_str, source = line.rstrip().split('\t')
            score = float(score_str)
            reliability[source] = score
    return reliability


def read_blacklist(filename):
    blacklisted = set()
    for line in open(filename, encoding='utf-8'):
        before_comment = line.split('#')[0].strip()
        if before_comment:
            blacklisted.add(before_comment)
    return blacklisted


def truncate_term(term):
    parts = term.split('/')
    return '/'.join(parts[:4])


def transform_node(node):
    if node.startswith('/s/web/'):
        return truncate_term(node)
    elif node.startswith('/s/contributor/omcs/20q'):
        return '/s/contributor/omcs/20q'
    elif node.startswith('/s/contributor/petgame'):
        return '/s/contributor/petgame'
    else:
        return node


def flatten_sources(sources):
    sources_out = []
    for source in sources:
        if source.startswith('/and/'):
            head, items = parse_compound_uri(source)
            sources_out.extend(items)
        elif source.startswith('/or/'):
            raise ValueError("Didn't expect a disjunction here")
        else:
            sources_out.append(source)
    return sources_out


def extract_contributors(source):
    """
    Extract the set of human contributors from a 'source' URI. This is used
    in making sure we haven't duplicated the same person's contribution of
    the same assertion.

    This has to happen during the combining step, not when extracting the
    ConceptNet edges in the first place, because the duplicate contributions
    may appear in different files.

    >>> extract_contributors('/s/contributor/omcs/dev')
    {'/s/contributor/omcs/dev'}
    >>> extract_contributors('/and/[/s/contributor/omcs/dev/,/s/activity/omcs1/]')
    {'/s/contributor/omcs/dev'}
    >>> extract_contributors('/s/robot/johnny5')
    set()
    """
    if source.startswith('/s/contributor/'):
        return {source}
    elif source.startswith('/and/'):
        head, items = parse_compound_uri(source)
        return set(item for item in items if item.startswith('/s/contributor/'))
    else:
        return set()


def combine_assertions(input_filenames, output_file):
    """
    Take in a number of tab-separated, sorted "CSV" files, indicated by
    `input_filenames`, that should be grouped together into assertions.
    Output a msgpack stream of assertions to `output_file`.

    The combined assertions will all have the dataset of the first edge that
    produces them, and the license of the strongest license being combined.

    This process requires its input to be a sorted CSV so that all edges for
    the same assertion will appear consecutively.
    """
    # The current_... variables accumulate information about the current
    # assertion. When the URI changes, we can output this assertion.
    current_uri = None
    current_data = {}
    current_contributors = set()
    current_surface = None
    current_dataset = None
    current_weight = 0.
    current_sources = []
    current_license = Licenses.cc_attribution
    blacklist = read_blacklist(
        get_support_data_filename('blacklist.txt')
    )

    out = MsgpackStreamWriter(output_file)
    out_bad = MsgpackStreamWriter(output_file + '.reject')
    for csv_filename in input_filenames:
        for line in open(csv_filename, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line:
                continue
            # Interpret the columns of the file.
            parts = line.split('\t')
            (uri, rel, start, end, weight, source_uri, id,
             this_dataset, this_license, surface) = parts[:10]
            surface = surface.strip()
            weight = float(weight)

            # If the uri is 'uri', this was a header line, which isn't supposed
            # to be there.
            assert uri != 'uri'

            # If the uri is the same as current_uri, accumulate more information.
            if uri == current_uri:
                current_weight += weight
                if source_uri not in current_sources:
                    contributors = extract_contributors(source_uri)

                    # Only list sources that are positive about the assertion
                    if weight > 0:
                        if not contributors & current_contributors:
                            current_sources.append(source_uri)
                            current_contributors |= contributors
                # We use the first surface form we see as the surface form for
                # the whole assertion.
                if (current_surface is None) and surface:
                    current_surface = surface

                # If one source has a ShareAlike license, the combined
                # assertion does too.
                if this_license == Licenses.cc_sharealike:
                    current_license = Licenses.cc_sharealike

            # Otherwise, it's a new assertion.
            else:
                if current_uri is not None:
                    included = (
                        get_uri_language(current_data['start']) in ALL_LANGUAGES and
                        get_uri_language(current_data['end']) in ALL_LANGUAGES
                    )
                    # Output the existing assertion before starting a new one.
                    nodes = current_sources + [current_data['start'], current_data['end']]
                    if (not included) or (set(nodes) & blacklist):
                        judged_weight = 0
                    else:
                        judged_weight = weight_scale(current_weight)
                    if judged_weight > 0:
                        destination = out
                    else:
                        destination = out_bad
                    output_assertion(
                        destination,
                        dataset=current_dataset, license=current_license,
                        sources=current_sources,
                        surfaceText=current_surface,
                        weight=judged_weight,
                        uri=current_uri,
                        **current_data
                    )

                # Set values for a new assertion.
                current_uri = uri
                current_data = {
                    'rel': rel,
                    'start': start,
                    'end': end
                }
                current_weight = weight
                current_sources = [source_uri]
                current_contributors = extract_contributors(source_uri)
                current_surface = surface or None
                current_dataset = this_dataset
                current_license = this_license

        if current_uri is not None:
            if set(nodes) & blacklist:
                judged_weight = 0
            else:
                judged_weight = weight_scale(current_weight)
            if judged_weight > 0:
                destination = out
            else:
                destination = out_bad
            output_assertion(
                destination,
                rel=rel, start=start, end=end,
                dataset=current_dataset, license=current_license,
                sources=current_sources,
                surfaceText=current_surface,
                weight=judged_weight,
                uri=current_uri
            )


def output_assertion(out, **kwargs):
    """
    Output an assertion to the given output stream. All keyword arguments
    become arguments to `make_edge`. (An assertion is a kind of edge.)
    """
    # Remove the URI, because make_edge computes it for us.
    uri = kwargs.pop('uri')

    # Combine the sources into one AND-OR tree.
    sources = set(kwargs.pop('sources'))
    source_tree = disjunction_uri(*sources)

    # Build the assertion object.
    assertion = make_edge(sources=source_tree, **kwargs)

    # Make sure the computed URI is the same as the one we had.
    assert assertion['uri'] == uri, (assertion['uri'], uri)

    # Output the result in a Msgpack stream.
    out.write(assertion)


class AssertionCombiner(object):
    """
    A class that wraps the combine_assertions function, so it can be tested in
    the same way as the readers, despite its extra parameters.
    """

    def __init__(self, license):
        self.license = license

    def handle_file(self, input_filename, output_file):
        combine_assertions([input_filename], output_file, self.license)


if __name__ == '__main__':
    # This is the main command-line entry point, used in steps of building
    # ConceptNet that need to combine edges into assertions. See data/Makefile
    # for more context.
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='*', help='csv files of input')
    parser.add_argument(
        '-o', '--output', help='msgpack file to output to'
    )
    args = parser.parse_args()
    combine_assertions(args.inputs, args.output)

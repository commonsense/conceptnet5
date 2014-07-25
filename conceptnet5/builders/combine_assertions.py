from __future__ import unicode_literals, print_function
import codecs
from conceptnet5.edges import make_edge
from conceptnet5.uri import disjunction_uri, parse_compound_uri
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
import os
import math

N = 100
CURRENT_DIR = os.getcwd()


def weight_scale(weight):
    """
    Put the weight of an assertion on a log_2 scale.
    """
    return math.log(max(1, weight + 1), 2)


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


def combine_assertions(csv_filename, output_file, license):
    """
    Take in a tab-separated, sorted "CSV" file, named `csv_filename`, of
    distinct edges which should be grouped together into assertions. Output a
    Msgpack stream of assertions to `output_file`.

    The combined assertions will all have the dataset of the first edge that
    produces them, and the license of the strongest license being combined
    (which should be passed in as `license`).

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

    out = MsgpackStreamWriter(output_file)
    for line in codecs.open(csv_filename, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line:
            continue
        # Interpret the columns of the file.
        parts = line.split('\t')
        (uri, rel, start, end, context, weight, source_uri, id, this_dataset,
         surface) = parts[:10]
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
                if not contributors & current_contributors:
                    current_sources.append(source_uri)
                    current_contributors |= contributors
            # We use the first surface form we see as the surface form for
            # the whole assertion.
            if (current_surface is None) and surface:
                current_surface = surface

        # Otherwise, it's a new assertion.
        else:
            if current_uri is not None:
                output_assertion(
                    out,
                    dataset=current_dataset, license=license,
                    sources=current_sources,
                    surfaceText=current_surface,
                    weight=weight_scale(current_weight),
                    uri=current_uri,
                    **current_data
                )
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

    if current_uri is not None:
        output_assertion(
            out,
            rel=rel, start=start, end=end,
            dataset=current_dataset, license=license,
            sources=current_sources,
            surfaceText=current_surface,
            weight=weight_scale(current_weight),
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
        combine_assertions(input_filename, output_file, self.license)


if __name__ == '__main__':
    # This is the main command-line entry point, used in steps of building
    # ConceptNet that need to combine edges into assertions. See data/Makefile
    # for more context.
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='csv file of input')
    parser.add_argument('output', help='msgpack file to output to')
    parser.add_argument(
        '-l', '--license',
        help='URI of the license to use, such as /l/CC/By-SA'
    )
    args = parser.parse_args()
    combiner = AssertionCombiner(args.license)
    combiner.handle_file(args.input, args.output)

from __future__ import unicode_literals, print_function
import codecs
from conceptnet5.edges import make_edge
from conceptnet5.nodes import disjunction_uri
import os
import json
import math

N = 100
CURRENT_DIR = os.getcwd()


def weight_scale(weight):
    """
    Put the weight of an assertion on a log_2 scale.
    """
    return math.log(max(1, weight + 1)) / math.log(2)


def combine_assertions(csv_filename, out_filename, dataset, license):
    """
    Take in a tab-separated, sorted "CSV" file, named `csv_filename`, of
    distinct edges which should be grouped together into assertions. Output a
    JSON stream of assertions to `out_filename`.

    The combined assertions will all have the same dataset and license,
    unlike the edges that comprise them. These are specified as the `dataset`
    and `license` arguments.

    This process requires its input to be a sorted CSV so that all edges for
    the same assertion will appear consecutively.
    """
    # The current_... variables accumulate information about the current
    # assertion. When the URI changes, we can output this assertion.
    current_uri = None
    current_data = {}
    current_surface = None
    current_weight = 0.
    current_sources = []

    out = codecs.open(out_filename, 'w', encoding='utf-8')
    for line in codecs.open(csv_filename, encoding='utf-8'):
        # Interpret the columns of the file.
        uri, rel, start, end, context, weight, source_uri, id, this_dataset, surface = line.split('\t')[:10]
        weight = float(weight)
        surface = surface.strip()

        # If the uri is 'uri', this was a header line, so ignore it.
        if uri == 'uri':
            continue

        # If the uri is the same as current_uri, accumulate more information.
        if uri == current_uri:
            current_weight += weight
            current_sources.append(source_uri)
            # We use the first surface form we see as the surface form for the whole assertion.
            if (current_surface is None) and surface:
                current_surface = surface

        # Otherwise, it's a new assertion.
        else:
            if current_uri is not None:
                output_assertion(out,
                    dataset=dataset, license=license,
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
            current_surface = surface or None

    output_assertion(out,
        rel=rel, start=start, end=end,
        dataset=dataset, license=license,
        sources=current_sources,
        surfaceText=current_surface,
        weight=weight_scale(current_weight),
        uri=current_uri
    )
    out.close()


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

    # Output the result in a JSON stream.
    line = json.dumps(assertion, ensure_ascii=False)
    print(line, out=out)


if __name__ == '__main__':
    # This is the main command-line entry point, used in steps of building
    # ConceptNet that need to combine edges into assertions. See data/Makefile
    # for more context.
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='csv file of input')
    parser.add_argument('output', help='jsons file to output to')
    parser.add_argument('-d', '--dataset',
        help='URI of the dataset to build, such as /d/conceptnet/5/combined-core'
    )
    parser.add_argument('-l', '--license',
        help='URI of the license to use, such as /l/CC/By-SA'
    )
    args = parser.parse_args()
    combine_assertions(args.input, args.output, args.dataset, args.license)


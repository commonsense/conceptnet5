from __future__ import unicode_literals, print_function
from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.nodes import uri_to_lemmas
import codecs
import json

def convert_to_solr(input_filename, output_filename):
    """
    Convert a JSON stream to a different JSON file that can be loaded into
    Solr.

    A JSON stream differs from standard JSON in that it contains several
    objects separated by line breaks.

    A Solr input file differs from standard JSON in a different way: it is
    represented as a single object with many fields. The values of these
    fields are the various different objects, but the key of each field
    must be "add".

    Having many values with the same key is incompatible with Python
    dictionaries, but is technically allowed by the JSON grammar. To create the
    output JSON file in Python, we have to write its components incrementally.
    """
    out = codecs.open(output_filename, 'w', encoding='utf-8')

    print("{", file=out)
    for info in read_json_stream(input_filename):
        boost = info['weight']

        # Handle searchable lemmas
        info['relLemmas'] = ''
        info['startLemmas'] = ' '.join(uri_to_lemmas(info['start']))
        info['endLemmas'] = ' '.join(uri_to_lemmas(info['end']))

        if boost > 0:
            if 'surfaceText' in info and info['surfaceText'] is None:
                del info['surfaceText']

            solr_struct = {'doc': info, 'boost': boost}
            solr_fragment = '\t"add": %s,' % json.dumps(solr_struct)
            print(solr_fragment, file=out)
    print('\t"commit": {}', file=out)
    print('}', file=out)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='Solr-style JSON file to output to')
    args = parser.parse_args()
    convert_to_solr(args.input, args.output)


if __name__ == '__main__':
    main()

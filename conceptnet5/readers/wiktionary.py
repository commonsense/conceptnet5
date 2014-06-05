# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.wiktparse.rules import ConceptNetWiktionarySemantics
from conceptnet5.formats.json_stream import read_json_stream, JSONStreamWriter
import os


def run_wiktionary(input_file, output_file, titledb, language='en', verbosity=0):
    trace = (verbosity >= 2)
    sem = ConceptNetWiktionarySemantics(language, titledb=titledb, trace=trace)
    output = JSONStreamWriter(output_file)
    for structure in read_json_stream(input_file):
        for edge in sem.parse_structured_entry(structure):
            if verbosity >= 1:
                print(edge['rel'], edge['start'], edge['end'])
            output.write(edge)


# Entry point for testing
handle_file = run_wiktionary

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Extracted .jsons file of Wiktionary sections")
    parser.add_argument('output_file', help='Output filename')
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help='Increase output verbosity')
    parser.add_argument('-l', '--language', default='en',
                        help='The ISO code of the language this Wiktionary is written in')
    parser.add_argument('-t', '--titles', default=None,
                        help='a titles.db file, indicating which headwords exist in which languages')
    args = parser.parse_args()
    titledb = args.titles
    if titledb is None:
        titledb = os.path.dirname(args.input_file) + '/titles.db'

    run_wiktionary(args.input_file, args.output_file, titledb=titledb,
                   language=args.language, verbosity=args.verbosity)

if __name__ == '__main__':
    main()

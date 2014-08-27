# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.wiktparse.rules import (EnWiktionarySemantics,
                                         DeWiktionarySemantics)
from conceptnet5.formats.msgpack_stream import read_msgpack_stream, MsgpackStreamWriter
import logging
import os
import sys


# Maps language to its ConceptNetWiktionarySemantics subclass
SEMANTICS = {'en': EnWiktionarySemantics, 'de': DeWiktionarySemantics}


def run_wiktionary(input_file, output_file, titledb=None, language='en',
                   verbosity=0, logger=None):
    if titledb is None:
        titledb = os.path.dirname(input_file) + '/titles.db'

    trace = (verbosity >= 2)
    sem = SEMANTICS[language](language, titledb=titledb, trace=trace,
                              logger=logger)
    output = MsgpackStreamWriter(output_file)
    for structure in read_msgpack_stream(input_file):
        for edge in sem.parse_structured_entry(structure):
            if verbosity >= 1:
                print(edge['rel'], edge['start'], edge['end'])
            output.write(edge)


handle_file = run_wiktionary


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Extracted .msgpack file of Wiktionary sections")
    parser.add_argument('output_file', help='Output filename')
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help='Increase output verbosity')
    parser.add_argument('-l', '--language', default='en',
                        help='The ISO code of the language this Wiktionary is written in')
    parser.add_argument('-t', '--titles', default=None,
                        help='a titles.db file, indicating which headwords exist in which languages')
    parser.add_argument('-o', '--logfile', default=None,
                        help='name of log file')
    parser.add_argument('-g', '--loglevel', default=logging.WARN,
                        choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'],
                        help='logging level (all-uppercase string)')

    args = parser.parse_args()

    logger = None
    if args.logfile:
        logger = logging.getLogger('run_wiktionary')
        handler = logging.FileHandler(args.logfile)
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
        if args.loglevel:
            logger.setLevel(logging._nameToLevel[args.loglevel])

    titledb = args.titles
    run_wiktionary(args.input_file, args.output_file, titledb=titledb,
                   language=args.language, verbosity=args.verbosity,
                   logger=logger)

if __name__ == '__main__':
    main()

from conceptnet5.util import get_support_data_filename
from conceptnet5.readers import (
    conceptnet4, dbpedia, jmdict, ptt_petgame, verbosity, extract_wiktionary,
    wordnet)
from conceptnet5.builders.combine_assertions import AssertionCombiner
import codecs
import os
import sys
import json
from tempfile import TemporaryDirectory
from nose.tools import eq_

if sys.version_info.major < 3:
    from StringIO import StringIO
else:
    from io import StringIO

TESTDATA_DIR = get_support_data_filename("testdata")


def data_path(filename):
    return os.path.join(TESTDATA_DIR, filename)


# This is a multi-test: it generates a sequence of tests, consisting of the
# function to run and the arguments to give it. nosetests knows how to run
# tests with this structure.
def test_reader_modules():
    combiner = AssertionCombiner('/l/CC/By-SA')
    io_mappings = [
        (conceptnet4, 'input/conceptnet4.jsons', ['output/conceptnet4.jsons']),
        (dbpedia, 'input/dbpedia.nt',
         ['output/dbpedia.jsons', 'output/dbpedia_map.nt']),
        (jmdict, 'input/jmdict.xml', ['output/jmdict.jsons']),
        (ptt_petgame, 'input/ptt_petgame.csv', ['output/ptt_petgame.jsons']),
        (verbosity, 'input/verbosity.txt', ['output/verbosity.jsons']),
        (wordnet, 'input/wordnet',
         ['output/wordnet.jsons', 'output/wordnet_map.nt']),
        (combiner, 'input/combiner.csv', ['output/combiner.jsons'])
    ]
    for (reader_module, _input, outputs) in io_mappings:
        yield compare_input_and_output, reader_module, _input, outputs


def compare_input_and_output(reader_module, _input, outputs):
    handle_file = getattr(reader_module, 'handle_file')
    input_filename = data_path(_input)
    output_filenames = [data_path(output) for output in outputs]
    output_streams = [StringIO() for _ in output_filenames]

    # Every reader module has a 'handle_file' function, with one input and
    # up to two outputs.
    #
    # We run these functions on the appropriate input files, with output
    # "files" that are actually StringIO instances. We then compare the
    # StringIO contents to the desired output, found in the reference output
    # files with the given filenames.
    handle_file(input_filename, *output_streams)
    for (reference_output_filename, output_stream) in zip(output_filenames,
                                                          output_streams):
        reference_output_file = codecs.open(reference_output_filename,
                                            encoding='utf-8')
        reference_lines = reference_output_file.readlines()
        actual_lines = output_stream.getvalue().split('\n')
        for line1, line2 in zip(reference_lines, actual_lines):
            if reference_output_filename.endswith('.jsons'):
                eq_(json.loads(line1), json.loads(line2))
            else:
                eq_(line1.rstrip('\n'), line2)
        reference_output_file.close()


# Wiktionary reader cannot be included in the test generator because it takes a
# different number of arguments and different input and output formats
def test_wiktionary_extraction():
    input_file = data_path('input/wiktionary.xml')
    reference_output = data_path('output/en_wiktionary.jsons')
    with TemporaryDirectory() as tempdir:
        extract_wiktionary.handle_file(input_file, tempdir, 'en', nfiles=1)
        with codecs.open(reference_output, encoding='utf-8') as fp:
            reference_jsons = sorted([json.loads(x) for x in fp.readlines()],
                                     key=lambda x: x['title'])
            actual_output = os.path.join(tempdir, 'wiktionary_00.jsons')
            actual_fp = codecs.open(actual_output, encoding='utf-8')
            actual_jsons = sorted([json.loads(x) for x in actual_fp.readlines()],
                                  key=lambda x: x['title'])
            actual_fp.close()
            for (expected, actual) in zip(reference_jsons, actual_jsons):
                eq_(expected, actual)

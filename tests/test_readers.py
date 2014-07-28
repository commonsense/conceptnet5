from conceptnet5.util import get_support_data_filename
from conceptnet5.readers import (
    conceptnet4, dbpedia, jmdict, ptt_petgame, verbosity, extract_wiktionary,
    wordnet)
from conceptnet5.builders.combine_assertions import AssertionCombiner
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import codecs
import os
import msgpack
import sys
from tempfile import TemporaryDirectory
from nose.tools import eq_
from io import BytesIO, StringIO

TESTDATA_DIR = get_support_data_filename("testdata")

if sys.version_info.major == 2:
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest


def data_path(filename):
    return os.path.join(TESTDATA_DIR, filename)


# This is a multi-test: it generates a sequence of tests, consisting of the
# function to run and the arguments to give it. nosetests knows how to run
# tests with this structure.
def test_reader_modules():
    combiner = AssertionCombiner('/l/CC/By-SA')
    io_mappings = [
        (conceptnet4, 'input/conceptnet4.jsons', ['output/conceptnet4.msgpack']),
        (dbpedia, 'input/dbpedia.nt',
         ['output/dbpedia.msgpack', 'output/dbpedia_map.nt']),
        (jmdict, 'input/jmdict.xml', ['output/jmdict.msgpack']),
        (ptt_petgame, 'input/ptt_petgame.csv', ['output/ptt_petgame.msgpack']),
        (verbosity, 'input/verbosity.txt', ['output/verbosity.msgpack']),
        (wordnet, 'input/wordnet',
         ['output/wordnet.msgpack', 'output/wordnet_map.nt']),
        (combiner, 'input/combiner.csv', ['output/combiner.msgpack'])
    ]
    for (reader_module, _input, outputs) in io_mappings:
        yield compare_input_and_output, reader_module, _input, outputs


def compare_input_and_output(reader_module, _input, outputs):
    handle_file = getattr(reader_module, 'handle_file')
    input_filename = data_path(_input)
    output_filenames = [data_path(output) for output in outputs]

    def writable_mock_stream(filename):
        if filename.endswith('.msgpack'):
            return BytesIO()
        else:
            return StringIO()

    output_streams = [writable_mock_stream(filename)
                      for filename in output_filenames]

    # Every reader module has a 'handle_file' function, with one input and
    # up to two outputs.
    #
    # We run these functions on the appropriate input files, with output
    # "files" that are actually BytesIO instances. We then compare the
    # BytesIO contents to the desired output, found in the reference output
    # files with the given filenames.
    handle_file(input_filename, *output_streams)
    for (reference_output_filename, output_stream) in zip(output_filenames, output_streams):
        msgpack_mode = reference_output_filename.endswith('.msgpack')
        if msgpack_mode:
            reference_output_file = open(reference_output_filename, 'rb')
        else:
            reference_output_file = codecs.open(reference_output_filename,
                                                'r', encoding='utf-8')
        with reference_output_file:
            reference_data = reference_output_file.read()
            output_data = output_stream.getvalue()
            if msgpack_mode:
                compare_msgpack(reference_data, output_data)
            else:
                compare_text(reference_data, output_data)


def compare_msgpack(bytes1, bytes2):
    unpacker1 = msgpack.Unpacker(BytesIO(bytes1), encoding='utf-8')
    unpacker2 = msgpack.Unpacker(BytesIO(bytes2), encoding='utf-8')
    for obj1, obj2 in zip_longest(unpacker1, unpacker2):
        eq_(obj1, obj2)


def compare_text(text1, text2):
    eq_(text1.strip('\n'), text2.strip('\n'))


# Wiktionary reader cannot be included in the test generator because it takes a
# different number of arguments and different input and output formats
def test_wiktionary_extraction():
    input_file = data_path('input/wiktionary.xml')
    reference_output = data_path('output/en_wiktionary.msgpack')
    with TemporaryDirectory() as tempdir:
        extract_wiktionary.handle_file(input_file, tempdir, 'en', nfiles=1)
        reference_output = list(read_msgpack_stream(reference_output))
        actual_output = list(read_msgpack_stream(os.path.join(tempdir, 'wiktionary_00.msgpack')))
        reference_output.sort(key=lambda x: x['title'])
        actual_output.sort(key=lambda x: x['title'])

        for (expected, actual) in zip_longest(reference_output, actual_output):
            eq_(expected, actual)

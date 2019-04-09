import os
from itertools import zip_longest
from tempfile import TemporaryDirectory

from nose.tools import eq_

from conceptnet5.formats.convert import json_to_msgpack, msgpack_to_json
from conceptnet5.formats.json_stream import JSONStreamWriter, read_json_stream
from conceptnet5.formats.msgpack_stream import (
    MsgpackStreamWriter, read_msgpack_stream
)

DATA = [
    {'a': 1},
    {'b': [2, 3]},
    {'c': [], 'd': {}}
]


def test_json_to_msgpack():
    with TemporaryDirectory(prefix='conceptnet-test') as tmpdir:
        json_path = os.path.join(tmpdir, 'test.jsons')
        msgpack_path = os.path.join(tmpdir, 'test.msgpack')
        
        writer = JSONStreamWriter(json_path)
        for item in DATA:
            writer.write(item)
        writer.close()

        json_to_msgpack(json_path, msgpack_path)
        reader = read_msgpack_stream(msgpack_path)
        for known, read in zip_longest(DATA, reader):
            eq_(known, read)


def test_msgpack_to_json():
    with TemporaryDirectory(prefix='conceptnet-test') as tmpdir:
        json_path = os.path.join(tmpdir, 'test.jsons')
        msgpack_path = os.path.join(tmpdir, 'test.msgpack')
        
        writer = MsgpackStreamWriter(json_path)
        for item in DATA:
            writer.write(item)
        writer.close()

        msgpack_to_json(json_path, msgpack_path)
        reader = read_json_stream(msgpack_path)
        for known, read in zip_longest(DATA, reader):
            eq_(known, read)

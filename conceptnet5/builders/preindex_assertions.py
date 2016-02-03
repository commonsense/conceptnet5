from __future__ import print_function
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import struct
from binascii import b2a_base64


def get_indices(edge):
    indices = []
    for field in ('uri', 'rel', 'start', 'end', 'dataset'):
        indices.append(edge[field])
    indices.extend(edge['sources'])
    return indices


def preindex_assertions(msgpack_filename):
    # TODO: use Click to accept outputs besides stdout
    for assertion, offset in read_msgpack_stream(msgpack_filename, offsets=True):
        weight = assertion['weight']
        if weight > 0.:
            packed = struct.pack('>fQ', 1.0 / weight, offset)
            packed_b64 = b2a_base64(packed).rstrip(b'\n').decode('ascii')
            for index in get_indices(assertion):
                print('%s\t%s' % (index, packed_b64))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('assertion_filename', help='msgpack file of assertions to index')
    # parser.add_argument('preindex_filename', help='pre-index filename to output to')
    args = parser.parse_args()
    preindex_assertions(args.assertion_filename)

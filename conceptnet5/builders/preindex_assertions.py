from __future__ import print_function
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import struct
from binascii import b2a_base64


def get_indices(edge):
    indices = []
    for field in ('uri', 'rel', 'start', 'end', 'dataset'):
        indices.append(edge[field])
    indices.extend(edge['sources'])
    indices.extend(edge['features'])
    return indices


def preindex_assertions(msgpack_filename, preindex_filename):
    with open(preindex_filename, 'w', encoding='utf-8') as out:
        goalpost = 0
        for assertion, offset in read_msgpack_stream(msgpack_filename, offsets=True):
            if offset // 1000000 > goalpost:
                print(offset)
                goalpost = offset // 1000000
            weight = assertion['weight']
            if weight > 0.:
                packed = struct.pack('>fQ', 1.0 / weight, offset)
                packed_b64 = b2a_base64(packed).rstrip('\n').decode('ascii')
                for index in get_indices(assertion):
                    print('%s\t%s' % (index, packed_b64), file=out)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('assertion_filename', help='msgpack file of assertions to index')
    parser.add_argument('preindex_filename', help='pre-index filename to output to')
    args = parser.parse_args()
    preindex_assertions(args.assertion_filename, args.preindex_filename)

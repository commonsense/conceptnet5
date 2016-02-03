from __future__ import print_function
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import kyotocabinet
from binascii import a2b_base64


def index_assertions(preindex_filename, index_filename):
    db = kyotocabinet.DB()
    current_key = ''
    current_data = []
    try:
        db.open(index_filename, db.OWRITER | db.OTRUNCATE)
        for i, line in enumerate(open(preindex_filename, encoding='utf-8')):
            if i % 100000 == 0:
                print(i)
            key, data_b64 = line.rstrip('\n').split('\t', 1)
            data = a2b_base64(data_b64.encode('ascii'))
            if key != current_key:
                if current_data:
                    current_data.sort()
                    entry = b''.join(current_data)
                    db.set(current_key, entry)
                    current_data.clear()
                current_key = key
            current_data.append(data)

        # add the final entry
        if current_data:
            current_data.sort()
            entry = b''.join(current_data)
            db.set(current_key, entry)
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('preindex_filename', help='sorted preindex file of assertions')
    parser.add_argument('index_filename', help='Index filename to output to (should end in ".kct")')
    args = parser.parse_args()
    index_assertions(args.preindex_filename, args.index_filename)

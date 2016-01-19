from __future__ import print_function
from conceptnet5.formats.lightning import ConceptNetLMDB
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import os
import sys


def index_assertions(input_dir, output_db, input_shards=8):
    db = ConceptNetLMDB(output_db, readonly=False)
    for filenum in range(input_shards):
        filename = 'part_%02d.msgpack' % filenum
        path = os.path.join(input_dir, filename)
        print("\tIndexing %s" % filename, end='')
        sys.stdout.flush()
        count = 0

        txn = db.write_transaction()
        for assertion in read_msgpack_stream(path):
            db.store_edge(txn, assertion)
            db.store_indices(txn, assertion)
            count += 1
            if count % 10000 == 0:
                print('.', end='')
                sys.stdout.flush()
        print()
        writer.close()


handle_file = index_assertions

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='directory of assertion files')
    parser.add_argument('output_db', help='LMDB directory to output to')
    parser.add_argument('--input-shards', help='number of files of assertions to read', type=int, default=8)
    args = parser.parse_args()
    index_assertions(args.input_dir, args.output_db, args.input_shards)

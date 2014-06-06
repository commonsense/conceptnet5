from conceptnet5.formats.sql import EdgeIndexWriter
from conceptnet5.formats.json_stream import read_json_stream
import os


def index_assertions(input_dir, output_db):
    filenames = sorted(os.listdir(input_dir))
    writer = EdgeIndexWriter(output_db)
    for filename in filenames:
        print("\tIndexing %s" % filename)
        for assertion in read_json_stream(filename):
            writer.add(assertion)
        writer.commit()


handle_file = index_assertions

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='directory of assertion files')
    parser.add_argument('output_db', help='SQLite file to output to')
    parser.add_argument(
        '-l', '--license',
        help='URI of the license to use, such as /l/CC/By-SA'
    )
    args = parser.parse_args()
    index_assertions(args.input_dir, args.output_db)

from __future__ import unicode_literals, print_function
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from conceptnet5.formats.json_stream import JSONStreamWriter


def convert_to_json(input_filename, output_filename):
    out_stream = JSONStreamWriter(output_filename)
    for obj in read_msgpack_stream(input_filename):
        out_stream.write(obj)
    out_stream.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Msgpack file of input')
    parser.add_argument('output', help='JSON-stream file to output to')
    args = parser.parse_args()
    convert_to_json(args.input, args.output)


if __name__ == '__main__':
    main()

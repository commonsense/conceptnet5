from __future__ import unicode_literals, print_function
from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter


def convert_to_msgpack(input_filename, output_filename):
    out_stream = MsgpackStreamWriter(output_filename)
    for obj in read_json_stream(input_filename):
        out_stream.write(obj)
    out_stream.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='Msgpack file to output to')
    args = parser.parse_args()
    convert_to_msgpack(args.input, args.output)


if __name__ == '__main__':
    main()

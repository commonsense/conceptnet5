from __future__ import unicode_literals, print_function
from conceptnet5.json_stream import read_json_stream
import codecs


def convert_to_tab_separated(input_filename, output_filename):
    out_stream = codecs.open(output_filename, 'w', encoding='utf-8')
    for info in read_json_stream(input_filename):
        text = info.get('surfaceText') or ''
        line = "%(uri)s\t%(rel)s\t%(start)s\t%(end)s\t%(context)s\t%(weight)s\t%(sources)s\t%(id)s\t%(dataset)s\t%(text)s" % {
            'uri': info['uri'],
            'rel': info['rel'],
            'start': info['start'],
            'end': info['end'],
            'context': info['context'],
            'weight': info['weight'],
            'sources': info['sources'],
            'id': info['id'],
            'dataset': info['dataset'],
            'text': text,
        }
        print(line, file=out_stream)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='CSV file to output to')
    args = parser.parse_args()
    convert_to_tab_separated(args.input, args.output)


if __name__ == '__main__':
    main()

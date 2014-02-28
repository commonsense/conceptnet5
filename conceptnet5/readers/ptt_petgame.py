from __future__ import unicode_literals
import codecs
import json
from conceptnet5.uri import concept_uri
from conceptnet5.json_stream import JSONStreamWriter
from conceptnet5.edges import make_edge
from conceptnet5.whereami import get_project_filename


FRAME_DATA = json.load(
    codecs.open(get_project_filename('data/info/zh_frames.json'))
)


def handle_raw_assertion(line):
    parts = line.split(', ')
    user, frame_id, concept1, concept2 = parts
    fdata = FRAME_DATA[frame_id]
    ftext = fdata['text']
    rel = fdata['relation']

    surfaceText = ftext.replace('{1}', '[[' + concept1 + ']]').replace('{2}', '[[' + concept2 + ']]')
    start = concept_uri('zh_TW', concept1)
    end = concept_uri('zh_TW', concept2)
    sources = ['/s/activity/ptt/petgame', '/s/contributor/petgame/' + user]
    yield make_edge(rel, start, end, dataset='/d/conceptnet/4/zh',
                    license='/l/CC/By', sources=sources,
                    surfaceText=surfaceText, weight=1)

def transform_file(input_filename, output_filename):
    out = JSONStreamWriter(output_filename)
    for line in codecs.open(input_filename, encoding='utf-8'):
        for new_obj in handle_raw_assertion(line):
            out.write(new_obj)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='JSON-stream file to output to')
    args = parser.parse_args()
    transform_file(args.input, args.output)


if __name__ == '__main__':
    main()


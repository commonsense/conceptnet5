from __future__ import unicode_literals, print_function
from conceptnet5.uri import join_uri, split_uri
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
import codecs
import langcodes


def reduce_concept(concept):
    """
    Remove the part of speech and disambiguation (if present) from a concept,
    leaving a potentially ambiguous concept that can be matched against surface
    text.

    Additionally, simplify language tags to a bare language. The main purpose
    is to remove the region tag from Chinese assertions, so they are considered
    simply as assertions about Chinese regardless of whether it is Traditional
    or Simplified Chinese. In the cases where they overlap, this helps to make
    the information more complete.

    >>> reduce_concept('/c/en/cat/n/feline')
    '/c/en/cat'
    >>> reduce_concept('/c/zh_TW/良好')
    '/c/zh/良好'
    """
    parts = split_uri(concept)
    langtag = parts[1]
    if parts[1] != '[':
        langcode = langcodes.get(langtag).language
        if langcode:
            parts[1] = langcode
    return join_uri(*parts[:3])


def convert_to_assoc(input_filename, output_filename):
    """
    Convert a JSON stream to a tab-separated "CSV" of concept-to-concept associations.

    The relation is mostly ignored, except:

    - Negative relations create associations between concepts suffixed with '/neg'
    - An assertion that means "People want X" in English or Chinese is converted to
      an assertion between X and "good", and also X and the negation of "bad"
    - Combining both of these, an assertion that "People don't want X" moves the
      negation so that X is associated with "not good" and "bad".

    The result can be used to predict word associations using ConceptNet by using
    dimensionality reduction, as in the `assoc_space` package.

    The relation is mostly ignored because we have not yet found a good way to
    take the relation into account in dimensionality reduction.
    """
    out_stream = codecs.open(output_filename, 'w', encoding='utf-8')

    for info in read_msgpack_stream(input_filename):
        startc = reduce_concept(info['start'])
        endc = reduce_concept(info['end'])
        rel = info['rel']
        weight = info['weight']

        if 'dbpedia' in info['source_uri'] and '/or/' not in info['source_uri']:
            # DBPedia associations are still too numerous and too weird to
            # associate.
            continue

        pairs = []
        if startc == '/c/en/person':
            if rel == '/r/Desires':
                pairs = [('/c/en/good', endc), ('/c/en/bad/neg', endc)]
            elif rel == '/r/NotDesires':
                pairs = [('/c/en/bad', endc), ('/c/en/good/neg', endc)]
            else:
                pairs = [(startc, endc)]
        elif startc == '/c/zh/人':
            if rel == '/r/Desires':
                pairs = [('/c/zh/良好', endc), ('/c/zh/不良/neg', endc)]
            elif rel == '/r/NotDesires':
                pairs = [('/c/zh/良好/neg', endc), ('/c/zh/不良', endc)]
            else:
                pairs = [(startc, endc)]
        else:
            negated = (rel.startswith('/r/Not') or rel.startswith('/r/Antonym'))
            if not negated:
                pairs = [(startc, endc)]
            else:
                pairs = [(startc, endc + '/neg'), (startc + '/neg', endc)]

        for (start, end) in pairs:
            line = "%(start)s\t%(end)s\t%(weight)s\t%(dataset)s\t%(relation)s" % {
                'start': start,
                'end': end,
                'weight': weight,
                'dataset': info['dataset'],
                'relation': rel
            }
            print(line, file=out_stream)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Msgpack file of input')
    parser.add_argument('output', help='CSV file to output to')
    args = parser.parse_args()
    convert_to_assoc(args.input, args.output)

if __name__ == '__main__':
    main()

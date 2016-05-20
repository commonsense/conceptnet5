from __future__ import unicode_literals, print_function
from conceptnet5.nodes import COMMON_LANGUAGES, get_uri_language, is_negative_relation
from conceptnet5.uri import uri_prefixes
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from collections import defaultdict
import codecs
import click


def msgpack_to_tab_separated(input_filename, output_filename):
    """
    Convert a msgpack stream to a tab-separated "CSV".
    """
    out_stream = codecs.open(output_filename, 'w', encoding='utf-8')
    for info in read_msgpack_stream(input_filename):
        if info.get('surfaceText') is None:
            info['surfaceText'] = ''
        info['weight'] = str(info['weight'])
        columns = [
            'uri', 'rel', 'start', 'end', 'weight', 'source_uri',
            'id', 'dataset', 'license', 'surfaceText'
        ]
        column_values = [info.get(col) for col in columns]
        line = '\t'.join(column_values)
        assert '\n' not in line
        print(line, file=out_stream)


def msgpack_to_assoc(input_filename, output_filename):
    """
    Convert a msgpack stream to a tab-separated "CSV" of concept-to-concept
    associations.

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

    weight_by_dataset = defaultdict(float)
    count_by_dataset = defaultdict(int)
    for info in read_msgpack_stream(input_filename):
        start_uri = info['start']
        end_uri = info['end']
        if not (
            start_uri.startswith('/c/') and end_uri.startswith('/c/')
            and get_uri_language(start_uri) in COMMON_LANGUAGES
            and get_uri_language(end_uri) in COMMON_LANGUAGES
        ):
            continue
        rel = info['rel']
        weight = info['weight']
        dataset = info['dataset']

        pairs = []
        for startc in uri_prefixes(start_uri, 3):
            for endc in uri_prefixes(end_uri, 3):
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
                    if is_negative_relation(rel):
                        pairs = [(startc, endc + '/neg'), (startc + '/neg', endc)]
                    else:
                        pairs = [(startc, endc)]

        for (start, end) in pairs:
            line = "%(start)s\t%(end)s\t%(weight)s\t%(dataset)s\t%(relation)s" % {
                'start': start,
                'end': end,
                'weight': weight,
                'dataset': dataset,
                'relation': rel
            }
            weight_by_dataset[dataset] += weight
            count_by_dataset[dataset] += 1
            print(line, file=out_stream)

    avg_weight_by_dataset = {
        dataset: weight_by_dataset[dataset] / count_by_dataset[dataset]
        for dataset in count_by_dataset
    }
    print("Average weights:")
    print(avg_weight_by_dataset)


@click.command()
@click.argument('converter', type=str)
@click.argument('input', type=click.Path(readable=True, dir_okay=False))
@click.argument('output', type=click.Path(writable=True, dir_okay=False))
def cli(converter, input, output):
    """
    Convert a stream of data from one format to another. Available converters
    are:

        msgpack_to_tab_separated
        msgpack_to_assoc
    """
    if converter == 'msgpack_to_tab_separated':
        convert_func = msgpack_to_tab_separated
    elif converter == 'msgpack_to_assoc':
        convert_func = msgpack_to_assoc
    convert_func(input, output)

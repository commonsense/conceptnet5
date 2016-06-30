from __future__ import print_function
from conceptnet5.uri import uri_prefixes
from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from conceptnet5.hashtable.preindex import preindex_data


def get_indices(edge):
    indices = []
    for field in ('uri', 'rel', 'start', 'end', 'dataset'):
        indices.extend(uri_prefixes(edge[field], 2))
    for source in edge['sources']:
        indices.extend(source.values())
    indices.extend(edge['features'])
    return indices


def preindex_assertions(msgpack_filename):
    for assertion, offset in read_msgpack_stream(msgpack_filename, offsets=True):
        weight = assertion['weight']
        for key in get_indices(assertion):
            yield (key, weight, offset)


def output_preindex(msgpack_filename):
    generator = preindex_assertions(msgpack_filename)
    preindex_data(generator)


if __name__ == '__main__':
    # TODO: click
    import sys
    output_preindex(sys.argv[1])

from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from conceptnet5.uri import uri_prefixes
from ordered_set import OrderedSet
import json


def write_row(outfile, items):
    print('\t'.join(sanitize(str(x)) for x in items), file=outfile)


def write_ordered_set(filename, oset):
    with open(filename, 'w', encoding='utf-8') as outfile:
        for i, item in enumerate(oset):
            print('%d\t%s' % (i, sanitize(item)), file=outfile)


def sanitize(text):
    return text.replace('\n', '').replace('\t', '').replace('\\', '\\\\')


def assertions_to_sql_csv(msgpack_filename, output_dir):
    output_nodes = output_dir + '/nodes.csv'
    output_edges = output_dir + '/edges.csv'
    output_sources = output_dir + '/sources.csv'
    output_prefixes = output_dir + '/prefixes.csv'

    node_list = OrderedSet()
    assertion_list = OrderedSet()
    seen_prefixes = set()

    edge_file = open(output_edges, 'w', encoding='utf-8')
    source_file = open(output_sources, 'w', encoding='utf-8')
    prefix_file = open(output_prefixes, 'w', encoding='utf-8')

    for assertion in read_msgpack_stream(msgpack_filename):
        if assertion['uri'] in assertion_list:
            continue
        assertion_idx = assertion_list.add(assertion['uri'])
        rel_idx = node_list.add(assertion['rel'])
        start_idx = node_list.add(assertion['start'])
        end_idx = node_list.add(assertion['end'])

        source_indices = []
        sources = assertion['sources']
        for source in sources:
            for sourceval in sorted(source.values()):
                source_idx = node_list.add(sourceval)
                source_indices.append(node_list.add(sourceval))
                write_prefixes(prefix_file, seen_prefixes, node_list, sourceval)

        jsondata = json.dumps(assertion, ensure_ascii=False, sort_keys=True)
        weight = assertion['weight']
        write_row(
            edge_file,
            [assertion_idx, assertion['uri'],
             rel_idx, start_idx, end_idx,
             weight, jsondata]
        )
        for node in (assertion['start'], assertion['end'], assertion['dataset']):
            write_prefixes(prefix_file, seen_prefixes, node_list, node)
        for source_idx in sorted(set(source_indices)):
            write_row(source_file, [assertion_idx, source_idx])

    edge_file.close()
    source_file.close()
    prefix_file.close()
    write_ordered_set(output_nodes, node_list)


def write_prefixes(prefix_file, seen_prefixes, node_list, node):
    for prefix in uri_prefixes(node):
        if (node, prefix) not in seen_prefixes:
            seen_prefixes.add((node, prefix))
            node_idx = node_list.add(node)
            prefix_idx = node_list.add(prefix)
            write_row(prefix_file, [node_idx, prefix_idx])


def load_sql_csv(connection, input_dir):
    for (filename, tablename) in [
        (input_dir + '/nodes.csv', 'nodes'),
        (input_dir + '/edges.csv', 'edges'),
        (input_dir + '/sources.csv', 'edge_sources'),
        (input_dir + '/prefixes.csv', 'node_prefixes')
    ]:
        print(filename)
        cursor = connection.cursor()
        with open(filename, 'rb') as file:
            cursor.execute("COPY %s FROM STDIN" % tablename, stream=file)
        cursor.close()
        connection.commit()

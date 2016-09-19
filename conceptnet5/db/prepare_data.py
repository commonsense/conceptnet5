from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from conceptnet5.uri import uri_prefixes
from conceptnet5.relations import SYMMETRIC_RELATIONS
from ordered_set import OrderedSet
import json


def write_row(outfile, items):
    print('\t'.join(sanitize(str(x)) for x in items), file=outfile)


def write_ordered_set(filename, oset):
    with open(filename, 'w', encoding='utf-8') as outfile:
        for i, item in enumerate(oset):
            print('%d\t%s' % (i, sanitize(item)), file=outfile)


def write_relations(filename, oset):
    with open(filename, 'w', encoding='utf-8') as outfile:
        for i, rel in enumerate(oset):
            directed_str = 't'
            if rel in SYMMETRIC_RELATIONS:
                directed_str = 'f'
            print('%d\t%s\t%s' % (i, sanitize(rel), directed_str), file=outfile)


def sanitize(text):
    return text.replace('\n', '').replace('\t', '').replace('\\', '\\\\')


def assertions_to_sql_csv(msgpack_filename, output_dir):
    output_nodes = output_dir + '/nodes.csv'
    output_edges = output_dir + '/edges.csv'
    output_relations = output_dir + '/relations.csv'
    output_sources = output_dir + '/sources.csv'
    output_edge_sources = output_dir + '/edge_sources.csv'
    output_node_prefixes = output_dir + '/node_prefixes.csv'
    output_features = output_dir + '/edge_features.csv'

    node_list = OrderedSet()
    source_list = OrderedSet()
    assertion_list = OrderedSet()
    relation_list = OrderedSet()
    seen_prefixes = set()

    edge_file = open(output_edges, 'w', encoding='utf-8')
    edge_source_file = open(output_edge_sources, 'w', encoding='utf-8')
    node_prefix_file = open(output_node_prefixes, 'w', encoding='utf-8')
    feature_file = open(output_features, 'w', encoding='utf-8')

    for assertion in read_msgpack_stream(msgpack_filename):
        if assertion['uri'] in assertion_list:
            continue
        assertion_idx = assertion_list.add(assertion['uri'])
        rel_idx = relation_list.add(assertion['rel'])
        start_idx = node_list.add(assertion['start'])
        end_idx = node_list.add(assertion['end'])

        source_indices = []
        sources = assertion['sources']
        for source in sources:
            for sourceval in sorted(source.values()):
                source_idx = source_list.add(sourceval)
                source_indices.append(source_idx)

        jsondata = json.dumps(assertion, ensure_ascii=False, sort_keys=True)
        weight = assertion['weight']
        write_row(
            edge_file,
            [assertion_idx, assertion['uri'],
             rel_idx, start_idx, end_idx,
             weight, jsondata]
        )
        for node in (assertion['start'], assertion['end'], assertion['dataset']):
            write_prefixes(node_prefix_file, seen_prefixes, node_list, node)
        for source_idx in sorted(set(source_indices)):
            write_row(edge_source_file, [assertion_idx, source_idx])

        if assertion['rel'] in SYMMETRIC_RELATIONS:
            features = [(0, start_idx), (0, end_idx)]
        else:
            features = [(1, start_idx), (-1, end_idx)]

        for direction, node_idx in features:
            write_row(feature_file, [rel_idx, direction, node_idx, assertion_idx])

    edge_file.close()
    edge_source_file.close()
    node_prefix_file.close()
    write_ordered_set(output_nodes, node_list)
    write_ordered_set(output_sources, source_list)
    write_relations(output_relations, relation_list)


def write_prefixes(prefix_file, seen_prefixes, node_list, node):
    for prefix in uri_prefixes(node):
        if (node, prefix) not in seen_prefixes:
            seen_prefixes.add((node, prefix))
            node_idx = node_list.add(node)
            prefix_idx = node_list.add(prefix)
            write_row(prefix_file, [node_idx, prefix_idx])


def load_sql_csv(connection, input_dir):
    for (filename, tablename) in [
        (input_dir + '/relations.csv', 'relations'),
        (input_dir + '/nodes.csv', 'nodes'),
        (input_dir + '/edges.csv', 'edges'),
        (input_dir + '/sources.csv', 'sources'),
        (input_dir + '/edge_sources.csv', 'edge_sources'),
        (input_dir + '/node_prefixes.csv', 'node_prefixes'),
        (input_dir + '/edge_features.csv', 'edge_features')
    ]:
        print(filename)
        cursor = connection.cursor()
        with open(filename, 'rb') as file:
            cursor.execute("COPY %s FROM STDIN" % tablename, stream=file)
        cursor.close()
        connection.commit()

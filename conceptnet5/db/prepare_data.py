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


def gin_indexable_edge(edge):
    gin_edge = {}
    gin_edge['uri'] = edge['uri']
    gin_edge['start'] = uri_prefixes(edge['start'])
    gin_edge['end'] = uri_prefixes(edge['end'])
    gin_edge['rel'] = uri_prefixes(edge['rel'])
    gin_edge['dataset'] = uri_prefixes(edge['dataset'])
    gin_edge['pairs'] = [
        '%s %s' % tuple(sorted([prefix1, prefix2]))
        for prefix1 in gin_edge['start']
        for prefix2 in gin_edge['end']
    ]
    flat_sources = set()
    for source in edge['sources']:
        for value in source.values():
            flat_sources.update(uri_prefixes(value, min_pieces=3))
    gin_edge['sources'] = sorted(flat_sources)
    return gin_edge


def assertions_to_sql_csv(msgpack_filename, output_dir):
    output_nodes = output_dir + '/nodes.csv'
    output_edges = output_dir + '/edges.csv'
    output_relations = output_dir + '/relations.csv'
    output_sources = output_dir + '/sources.csv'
    output_features = output_dir + '/edge_features.csv'
    output_edges_gin = output_dir + '/edges_gin.csv'

    node_list = OrderedSet()
    source_list = OrderedSet()
    assertion_list = OrderedSet()
    relation_list = OrderedSet()

    edge_file = open(output_edges, 'w', encoding='utf-8')
    edge_gin_file = open(output_edges_gin, 'w', encoding='utf-8')
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
        write_row(
            edge_gin_file,
            [assertion_idx, weight,
             json.dumps(gin_indexable_edge(assertion), ensure_ascii=False)]
        )

        features = []
        start_p_indices = [
            node_list.add(prefix) for prefix in uri_prefixes(assertion['start'], 3)
        ]
        end_p_indices = [
            node_list.add(prefix) for prefix in uri_prefixes(assertion['end'], 3)
        ]
        if assertion['rel'] in SYMMETRIC_RELATIONS:
            for start_p_idx in start_p_indices:
                features.append((0, start_p_idx))
            for end_p_idx in end_p_indices:
                features.append((0, end_p_idx))
        else:
            for start_p_idx in start_p_indices:
                features.append((1, start_p_idx))
            for end_p_idx in end_p_indices:
                features.append((-1, end_p_idx))

        for direction, node_idx in features:
            write_row(feature_file, [rel_idx, direction, node_idx, assertion_idx])

    edge_file.close()
    edge_gin_file.close()
    write_ordered_set(output_nodes, node_list)
    write_ordered_set(output_sources, source_list)
    write_relations(output_relations, relation_list)


def load_sql_csv(connection, input_dir):
    for (filename, tablename) in [
        (input_dir + '/relations.csv', 'relations'),
        (input_dir + '/nodes.csv', 'nodes'),
        (input_dir + '/edges.csv', 'edges'),
        (input_dir + '/sources.csv', 'sources'),
        (input_dir + '/edges_gin.shuf.csv', 'edges_gin'),
        (input_dir + '/edge_features.csv', 'edge_features'),
    ]:
        cursor = connection.cursor()
        with open(filename, 'rb') as file:
            cursor.copy_from(file, tablename)
        cursor.close()
        connection.commit()

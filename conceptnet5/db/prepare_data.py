import json

from conceptnet5.formats.msgpack_stream import read_msgpack_stream
from conceptnet5.relations import SYMMETRIC_RELATIONS
from conceptnet5.uri import uri_prefixes
from ordered_set import OrderedSet


def write_row(outfile, items):
    """
    Write a tab-separated row to a file.
    """
    print('\t'.join(sanitize(str(x)) for x in items), file=outfile)


def write_ordered_set(filename, oset):
    """
    Write an OrderedSet of strings as a two-column table, containing
    the ID and the string value.
    """
    with open(filename, 'w', encoding='utf-8') as outfile:
        for i, item in enumerate(oset):
            print('%d\t%s' % (i, sanitize(item)), file=outfile)


def write_relations(filename, oset):
    """
    To create the `relations` table, we need one additional column of
    information beyond `write_ordered_set`, which is a boolean of whether
    the relation is directed.
    """
    with open(filename, 'w', encoding='utf-8') as outfile:
        for i, rel in enumerate(oset):
            directed_str = 't'
            if rel in SYMMETRIC_RELATIONS:
                directed_str = 'f'
            print('%d\t%s\t%s' % (i, sanitize(rel), directed_str), file=outfile)


def sanitize(text):
    """
    We're using a very simple approach to writing a CSV (which is actually
    tab-separated, but a lot of software considers that a kind of CSV). Our
    CSV output will be formatted correctly and understood by psql as long
    as we avoid certain characters that would conflict:

    - Newlines (which of course separate CSV entries)
    - Tabs (which separate our columns)
    - Null codepoints (which are not allowed in psql)

    We also need to escape every literal backslash, as backslashes are
    interpreted by psql.

    It's a good question whether this step should be necessary -- names
    of concepts shouldn't include control characters, and the few
    instances of backslashes in ConceptNet appear to be mistakes.
    """
    return (
        text.replace('\n', '')
        .replace('\t', '')
        .replace('\x00', '')
        .replace('\\', '\\\\')
    )


def gin_indexable_edge(edge):
    """
    Convert an edge into a dictionary that can be matched with the JSONB @>
    operator, which tests if one dictionary includes all the information in
    another. This operator can be indexed by GIN.

    We replace the 'start', 'end', 'rel', and 'dataset' URIs with lists
    of their URI prefixes. We query those slots with a single-element list,
    which will be a sub-list of the prefix list if it's a match.

    As an example, a query for {'start': '/c/en'} will become the GIN
    query {'start': ['/c/en']}, which will match indexed edges such as
    {
        'start': ['/c/en', '/c/en/dog'],
        'end': ['/c/en', '/c/en/bark'],
        'rel': ['/r/CapableOf'],
        ...
    }
    """
    gin_edge = {}
    gin_edge['uri'] = edge['uri']
    gin_edge['start'] = uri_prefixes(edge['start'])
    gin_edge['end'] = uri_prefixes(edge['end'])
    gin_edge['rel'] = uri_prefixes(edge['rel'])
    gin_edge['dataset'] = uri_prefixes(edge['dataset'])
    flat_sources = set()
    for source in edge['sources']:
        for value in source.values():
            flat_sources.update(uri_prefixes(value, min_pieces=3))
    gin_edge['sources'] = sorted(flat_sources)
    return gin_edge


def assertions_to_sql_csv(msgpack_filename, output_dir):
    """
    Scan through the list of assertions (edges that are unique in their
    start, end, and relation) and produce CSV files that can be loaded
    into PostgreSQL tables.

    The columns of these CSV files are unlabeled, but they correspond
    to the order of the table columns defined in schema.py.
    """
    # Construct the filenames of the CSV files, one per table
    output_nodes = output_dir + '/nodes.csv'
    output_edges = output_dir + '/edges.csv'
    output_relations = output_dir + '/relations.csv'
    output_sources = output_dir + '/sources.csv'
    output_features = output_dir + '/edge_features.csv'
    output_edges_gin = output_dir + '/edges_gin.csv'

    # We can't rely on Postgres to assign IDs, because we need to know the
    # IDs to refer to them _before_ they're in Postgres. So we track our own
    # unique IDs using OrderedSet.
    node_list = OrderedSet()
    source_list = OrderedSet()
    assertion_list = OrderedSet()
    relation_list = OrderedSet()

    # These are three files that we will write incrementally as we iterate
    # through the edges. The syntax restrictions on 'with' leave me with no
    # way to format this that satisfies my style checker and auto-formatter.
    with open(output_edges, 'w', encoding='utf-8') as edge_file,\
         open(output_edges_gin, 'w', encoding='utf-8') as edge_gin_file,\
         open(output_features, 'w', encoding='utf-8') as feature_file:
        for assertion in read_msgpack_stream(msgpack_filename):
            # Assertions are supposed to be unique. If they're not, we should
            # find out and the build should fail.
            if assertion['uri'] in assertion_list:
                raise ValueError("Duplicate assertion: {!r}".format(assertion))

            # Get unique IDs for the relation, start, and end, and the assertion
            # itself. The relation, start, and end IDs may already exists; this is
            # handled by OrderedSet.
            assertion_idx = assertion_list.add(assertion['uri'])
            rel_idx = relation_list.add(assertion['rel'])
            start_idx = node_list.add(assertion['start'])
            end_idx = node_list.add(assertion['end'])

            # Also get unique IDs for each of the sources listed as contributing
            # to this assertion.
            source_indices = []
            sources = assertion['sources']
            for source in sources:
                for sourceval in sorted(source.values()):
                    source_idx = source_list.add(sourceval)
                    source_indices.append(source_idx)

            # Write the edge data to the `edge_file`.
            jsondata = json.dumps(assertion, ensure_ascii=False, sort_keys=True)
            weight = assertion['weight']
            write_row(
                edge_file,
                [
                    assertion_idx,
                    assertion['uri'],
                    rel_idx,
                    start_idx,
                    end_idx,
                    weight,
                    jsondata,
                ],
            )

            # Convert the edge to the form that we can easily filter using GIN
            # indexing, and write that to the `edge_gin_file`.
            write_row(
                edge_gin_file,
                [
                    assertion_idx,
                    weight,
                    json.dumps(
                        gin_indexable_edge(assertion),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                ],
            )

            # Extract the 'features' (combinations of the relation and one node)
            # that are present in the edge. We may need to match the node using
            # a prefix of that node, so store the feature separately for each
            # prefix.
            features = []

            # Get the IDs in the node table for each prefix of the nodes
            start_p_indices = [
                node_list.add(prefix) for prefix in uri_prefixes(assertion['start'], 3)
            ]
            end_p_indices = [
                node_list.add(prefix) for prefix in uri_prefixes(assertion['end'], 3)
            ]

            # Write the feature data, the 'direction' (forward, backward, or
            # symmetric), and the edge ID to the feature table.
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

    # Write our tables of unique IDs
    write_ordered_set(output_nodes, node_list)
    write_ordered_set(output_sources, source_list)
    write_relations(output_relations, relation_list)


def load_sql_csv(connection, input_dir):
    """
    Load the CSV files we created into PostgreSQL using the `copy_from`
    method, which is the same as the COPY command at the psql command line.
    """
    for (filename, tablename) in [
        (input_dir + '/relations.csv', 'relations'),
        (input_dir + '/nodes.csv', 'nodes'),
        (input_dir + '/edges.csv', 'edges'),
        (input_dir + '/sources.csv', 'sources'),
        (input_dir + '/edges_gin.shuf.csv', 'edges_gin'),
        (input_dir + '/edge_features.csv', 'edge_features'),
    ]:
        with connection.cursor() as cursor:
            with open(filename, 'rb') as file:
                cursor.copy_from(file, tablename)
        connection.commit()

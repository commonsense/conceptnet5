'''
This is a test to ensure that all of the relations produced by the full 
ConceptNet build are in fact recorded in the relations.py file.
'''

from conceptnet5.relations import ALL_RELATIONS
from conceptnet5.util import get_data_filename


def collect_relations(path):
    '''
    Reads a .txt file from the path given, which should be in the format of 
    ConceptNet's data/stats/relations.txt file, and extract the set of the 
    (unique) relations that occur in it.
    '''
    relations = set()
    with open(path, 'rt', encoding='utf-8') as fp:
        for line in fp:
            _count, relation = line.lstrip().split(maxsplit=2)
            relations.add(relation)
    return relations


def test_relations_recorded():
    built_relations_file = get_data_filename('stats/relations.txt')
    built_relations = collect_relations(built_relations_file)
    recorded_relations = set(ALL_RELATIONS)
    missing_relations = built_relations - recorded_relations
    assert len(missing_relations) == 0

"""
This is a sanity check to run after the full ConceptNet build, confirming that
we have data in all the appropriate languages, from all the appropriate sources.
"""

import pytest

from conceptnet5.languages import ALL_LANGUAGES, COMMON_LANGUAGES, CORE_LANGUAGES
from conceptnet5.util import get_data_filename
from conceptnet5.db.query import AssertionFinder


DATASETS = [
    '/d/conceptnet/4/en',
    '/d/conceptnet/4/pt',
    '/d/conceptnet/4/ja',
    '/d/conceptnet/4/zh',
    '/d/conceptnet/4/nl',
    '/d/dbpedia',
    '/d/jmdict',
    '/d/opencyc',
    '/d/verbosity',
    '/d/wordnet',
    '/d/wiktionary/en',
    '/d/wiktionary/fr',
    '/d/wiktionary/de',
]


@pytest.mark.requires_full_build
def test_languages_exist():
    lang_stats_file = get_data_filename('stats/languages.txt')
    counts = {}
    for line in open(lang_stats_file, encoding='utf-8'):
        count_str, lang = line.strip().split()
        counts[lang] = int(count_str)

    for lang in ALL_LANGUAGES:
        assert lang in counts, lang

    for lang in COMMON_LANGUAGES:
        assert counts[lang] >= 1000, counts[lang]

    for lang in CORE_LANGUAGES:
        assert counts[lang] >= 100000, (lang, counts[lang])


@pytest.mark.requires_full_build
@pytest.mark.parametrize('dataset', DATASETS)
def test_dataset_exists(dataset):
    finder = AssertionFinder()
    # Test that each dataset has at least 100 assertions
    q = finder.query({'dataset': dataset}, limit=100)
    assert len(q) == 100, dataset

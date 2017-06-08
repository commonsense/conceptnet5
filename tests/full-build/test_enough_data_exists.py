"""
This is a sanity check to run after the full ConceptNet build, confirming that
we have data in all the appropriate languages, from all the appropriate sources.
"""

from conceptnet5.util import get_data_filename
from conceptnet5.languages import CORE_LANGUAGES, COMMON_LANGUAGES, ALL_LANGUAGES
from conceptnet5.db.query import AssertionFinder

test_finder = None


def setUp():
    global test_finder
    test_finder = AssertionFinder()


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


def test_datasets_exist():
    for dataset in [
        '/d/conceptnet/4/en', '/d/conceptnet/4/pt', '/d/conceptnet/4/ja',
        '/d/conceptnet/4/zh', '/d/conceptnet/4/nl',
        '/d/dbpedia', '/d/jmdict', '/d/opencyc', '/d/verbosity', '/d/wordnet',
        '/d/wiktionary/en', '/d/wiktionary/fr', '/d/wiktionary/de'
    ]:
        # Test that each dataset has at least 100 assertions
        q = test_finder.query({'dataset': dataset}, limit=100)
        assert len(q) == 100, dataset


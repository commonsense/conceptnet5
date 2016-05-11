# coding: utf-8
from __future__ import unicode_literals
"""
This module constructs URIs for nodes (concepts) in various languages. This
puts the tools in conceptnet5.uri together with functions that normalize
terms and languages into a standard form.
"""

from conceptnet5.language.english import english_filter
from conceptnet5.language.token_utils import simple_tokenize
from conceptnet5.uri import concept_uri, split_uri, parse_possible_compound_uri
from ftfy import fix_text
import re


SYMMETRIC_RELATIONS = {
    '/r/RelatedTo',
    '/r/SimilarTo',
    '/r/TranslationOf',
    '/r/EtymologicallyRelatedTo',
    '/r/Synonym',
    '/r/Antonym',
    '/r/DistinctFrom'
}


LCODE_ALIASES = {
    # Pretend that various Chinese languages and variants are equivalent. This
    # is linguistically problematic, but it's also very helpful for aligning
    # them on terms where they actually are the same.
    #
    # This would mostly be a problem if ConceptNet was being used to *generate*
    # Chinese natural language text, and I don't believe it is.
    'cmn': 'zh',
    'yue': 'zh',
    'zh_tw': 'zh',
    'zh_cn': 'zh',
    'zh-tw': 'zh',
    'zh-cn': 'zh',

    'nds-de': 'nds',
    'nds-nl': 'nds',

    # An easier case: consider Bahasa Indonesia and Bahasa Malay to be the
    # same language, with code 'ms', because they're already 90% the same.
    # Many sources use 'ms' to represent the entire macrolanguage, with
    # 'zsm' to refer to Bahasa Malay in particular.
    'zsm': 'ms',
    'id': 'ms',

    # We had to make a decision here on Norwegian. Norwegian Bokmål ('nb') and
    # Nynorsk ('nn') have somewhat different vocabularies but are mutually
    # intelligible. Informal variants of Norwegian, especially when spoken,
    # don't really distinguish them. Some Wiktionary entries don't distinguish
    # them either. And the CLDR data puts them both in the same macrolanguage
    # of Norwegian ('no').
    #
    # The catch is, Bokmål and Danish are *more* mutually intelligible than
    # Bokmål and Nynorsk, so maybe they should be the same language too. But
    # Nynorsk and Danish are less mutually intelligible.
    #
    # There is no language code that includes both Danish and Nynorsk, so
    # it would probably be inappropriate to group them all together. We will
    # take the easy route of making the language boundaries correspond to the
    # national boundaries, and say that 'nn' and 'nb' are both kinds of 'no'.
    #
    # More information: http://languagelog.ldc.upenn.edu/nll/?p=9516
    'nn': 'no',
    'nb': 'no',

    # Our sources have entries in Croatian, entries in Serbian, and entries
    # in Serbo-Croatian. Some of the Serbian and Serbo-Croatian entries
    # are written in Cyrillic letters, while all Croatian entries are written
    # in Latin letters. Bosnian and Montenegrin are in there somewhere,
    # too.
    #
    # Applying the same principle as Chinese, we will unify the language codes
    # without unifying the scripts.
    'bs': 'sh',
    'hr': 'sh',
    'sr': 'sh',
    'sr-latn': 'sh',
    'sr-cyrl': 'sh',

    # Wikipedia believes that many separately catalogued languages are
    # dialects of the Western Desert language of Australia. If combined, this
    # language would meet the criteria for inclusion in ConceptNet. But this
    # language has no code.
    #
    # That means we can make one up. We'll call it 'aus-x-wati', after one
    # name for the language, 'Wati'. If something ignores the 'x-wati'
    # extension, it will still be distinguished as some sort of Australian
    # language.
    'ktd': 'aus-x-wati',
    'kux': 'aus-x-wati',
    'mpj': 'aus-x-wati',
    'ntj': 'aus-x-wati',
    'piu': 'aus-x-wati',
    'pjt': 'aus-x-wati',
    'kdd': 'aus-x-wati',
    'pti': 'aus-x-wati',
    'pii': 'aus-x-wati',

    # More language codes that we would rather group into a broader language:
    'arb': 'ar',   # Modern Standard Arabic -> Arabic
    'arz': 'ar',   # Egyptian Arabic -> Arabic
    'ary': 'ar',   # Moroccan Arabic -> Arabic
    'ckb': 'ku',   # Central Kurdish -> Kurdish
    'mvf': 'mn',   # Peripheral Mongolian -> Mongolian
    'tl': 'fil',   # Tagalog -> Filipino
    'vro': 'et',   # Võro -> Estonian
    'sgs': 'lt',   # Samogitian -> Lithuanian
    'ciw': 'oj',   # Chippewa -> Ojibwe
    'xal': 'xwo',  # Kalmyk -> Oirat
    'ffm': 'ff',   # Maasina Fulfulde -> Fula
}


# These are all the languages we currently support in ConceptNet. Concepts
# from languages not in this list get filtered out.
#
# The main criteria are that the language should:
#
# - be involved in at least 500 edges
# - have a consistent BCP 47 language code
# - not be a sign language
#   (we don't have a good computational representation of signing)
# - *either* have extant native speakers, be historically important,
#   or be a fully-developed artificial language

LANGUAGES = {
    # Languages with extant native speakers and at least 25,000 edges
    'common': {
        'en',   # English
        'fr',   # French
        'de',   # German
        'it',   # Italian
        'es',   # Spanish
        'ru',   # Russian
        'pt',   # Portuguese
        'ja',   # Japanese
        'zh',   # Chinese
        'nl',   # Dutch

        'fi',   # Finnish
        'pl',   # Polish
        'bg',   # Bulgarian
        'sv',   # Swedish
        'cs',   # Czech
        'sh',   # Serbo-Croatian
        'sl',   # Slovenian
        'ar',   # Arabic
        'ca',   # Catalan
        'hu',   # Hungarian
        'se',   # Northern Sami
        'is',   # Icelandic
        'ro',   # Romanian
        'el',   # Greek
        'lv',   # Latvian
        'ms',   # Malay
        'tr',   # Turkish
        'nb',   # Norwegian Bokmål
        'da',   # Danish
        'ga',   # Irish
        'vi',   # Vietnamese
        'ko',   # Korean
        'hy',   # Armenian
        'gl',   # Galician
        'oc',   # Occitan
        'fo',   # Faroese
        'gd',   # Scottish Gaelic
        'fa',   # Persian
        'nn',   # Norwegian Nynorsk
        'ast',  # Asturian
        'hsb',  # Upper Sorbian
        'ka',   # Georgian
        'he',   # Hebrew
        'no',   # Norwegian Bokmål
        'sq',   # Albanian
        'mg',   # Malagasy
        'nrf',  # Jèrriais
        'sk',   # Slovak
        'lt',   # Lithuanian
        'et',   # Estonian
        'te',   # Telugu
        'mk',   # Macedonian
        'nv',   # Navajo
        'hi',   # Hindi
        'af',   # Afrikaans
        'gv',   # Manx
        'sa',   # Sanskrit
        'th',   # Thai
        'fil',  # Filipino
        'eu',   # Basque
        'rup',  # Aromanian
        'uk',   # Ukrainian
        'cy',   # Welsh
    },

    # Languages with no extant native speakers, but at least 25,000 edges
    # including etymologies.
    'common-historical': {
        'la',   # Latin
        'grc',  # Ancient Greek
        'xcl',  # Classical Armenian
        'fro',  # Old French
        'ang',  # Old English
        'non',  # Old Norse
    },

    # Artificial languages with at least 25,000 edges
    'common-artificial': {
        'mul',  # Multilingual -- used for international standards and emoji
        'eo',   # Esperanto
        'io',   # Ido
        'vo',   # Volapük
    },

    'more': {
        'rm',   # Romansh
        'br',   # Breton
        'lb',   # Luxembourgish
        'fy',   # Western Frisian
        'ku',   # Kurdish
        'be',   # Belarusian
        'kk',   # Kazakh
        'frp',  # Arpitan (Franco-Provençal)
        'mi',   # Maori
        'sw',   # Swahili
        'yi',   # Yiddish
        'dsb',  # Lower Sorbian
        'vec',  # Venetian
        'ln',   # Lingala
        'ur',   # Urdu
        'fur',  # Friulian
        'pap',  # Papiamento
        'nds',  # Low German
        'mn',   # Mongolian
        'km',   # Khmer
        'ba',   # Bashkir
        'os',   # Ossetic
        'sco',  # Scots
        'lld',  # Ladin
        'bn',   # Bengali
        'mt',   # Maltese
        'ady',  # Adyghe
        'az',   # Azerbaijani
        'qu',   # Quechua
        'scn',  # Sicilian
        'haw',  # Hawaiian
        'bm',   # Bambara
        'iu',   # Inuktitut
        'lo',   # Lao
        'crh',  # Crimean Turkish
        'ses',  # Koyraboro Senni
        'ta',   # Tamil
        'tg',   # Tajik
        'vep',  # Veps
        'wa',   # Walloon
        'kw',   # Cornish
        'co',   # Corsican
        'tt',   # Tatar
        'ky',   # Kyrgyz
        'ceb',  # Cebuano
        'nan',  # Min Nan Chinese
        'dlm',  # Dalmatian
        'mdf',  # Moksha
        'stq',  # Saterland Frisian
        'uz',   # Uzbek
        'pcd',  # Picard
        'my',   # Burmese
        'zu',   # Zulu
        'sc',   # Sardinian
        'tk',   # Turkmen
        'ht',   # Haitian Creole
        'lad',  # Ladino
        'arn',  # Mapuche
        'srn',  # Sranan Tongo
        'ps',   # Pashto
        'gu',   # Gujarati
        'kl',   # Kalaallisut
        'mr',   # Marathi
        'tpi',  # Tok Pisin
        'hil',  # Hiligaynon
        'kn',   # Kannada
        'ne',   # Nepali
        'wym',  # Wymysorys
        'ug',   # Uyghur
        'nap',  # Neapolitan
        'oj',   # Ojibwa
        'mwl',  # Mirandese
        'frr',  # Northern Frisian
        'an',   # Aragonese
        'yua',  # Yucateco
        'cv',   # Chuvash
        'bo',   # Tibetan
        'zdj',  # Ngazidja Comorian
        'chr',  # Cherokee
        'sah',  # Sakha
        'pal',  # Pahlavi
        'ce',   # Chechen
        'wo',   # Wolof
        'li',   # Limburgish
        'ml',   # Malayalam
        'egl',  # Emilian
        'csb',  # Kashubian
        'ist',  # Istriot
        'lkt',  # Lakota
        'pi',   # Pali
        'kbd',  # Kabardian
        'twf',  # Northern Tiwa / Taos
        'jv',   # Javanese
        'fon',  # Fon
        'qya',  # Quenya
        'nah',  # Nahuatl languages
        'pa',   # Punjabi
        'myv',  # Erzya
        'nmn',  # !Xóõ
        'rom',  # Romany
        'ltg',  # Latgalian
        'ee',   # Ewe
        'sm',   # Samoan
        'am',   # Amharic
        'kum',  # Kumyk
        'krc',  # Karachay-Balkar
        'gsw',  # Swiss German
        'dak',  # Dakota
        'swb',  # Comorian
        'bal',  # Baluchi
        'si',   # Sinhala
        'so',   # Somali
        'su',   # Sundanese
        'kjh',  # Khakas
        'cic',  # Chickasaw
        'gag',  # Gagauz
        'nog',  # Nogai
        'chk',  # Chuukese
        'ha',   # Hausa
        'tyv',  # Tuvinian
        'nhn',  # Central Nahuatl
        'zza',  # Zaza
        'oma',  # Omaha-Ponca
        'vot',  # Votic
        'krl',  # Karelian
        'rw',   # Kinyarwanda
        'aa',   # Afar
        'or',   # Oriya
        'alt',  # Southern Altai
        'esu',  # Central Yupik
        'ccc',  # Chamicuro
        'ab',   # Abkhazian
        'ppl',  # Pipil
        'chl',  # Cahuilla
        'ain',  # Ainu
        'na',   # Nauru
        'ty',   # Tahitian
        'wau',  # Waurá
        'dua',  # Duala
        'rap',  # Rapa Nui
        'adx',  # Amdo Tibetan
        'cjs',  # Shor
        'tet',  # Tetum
        'kim',  # Karagas (Tofa)
        'hak',  # Hakka
        'lij',  # Ligurian (modern)
        'gn',   # Guarani
        'tpw',  # Tupi
        'sms',  # Skolt Sami
        'xmf',  # Mingrelian
        'smn',  # Inari Sami
        'raj',  # Rajasthani
        'cim',  # Cimbrian
        'rue',  # Rusyn
        'hke',  # Hunde
        'fj',   # Fijian
        'pms',  # Piedmontese
        'wae',  # Walser
        'yo',   # Yoruba
        'mh',   # Marshallese
        'szl',  # Silesian
        'aus-x-wati',  # Western Desert macrolanguage of Australia
        'khb',  # Tai Lü
        'dv',   # Divehi
        'udm',  # Udmurt
        'dje',  # Zarma
        'ilo',  # Iloko / Ilocano
        'aii',  # Assyrian Neo-Aramaic
        'koy',  # Koyukon
        'war',  # Waray
        'lmo',  # Lombard
        'ti',   # Tigrinya
        'av',   # Avar
        'mch',  # Maquiritari
        'abe',  # Western Abenaki
        'cho',  # Choctaw
        'xwo',  # Oirat
        'za',   # Zhuang
        'ki',   # Kikuyu
        'lzz',  # Laz
        'sd',   # Sindhi
        'st',   # Sotho
        'shh',  # Shoshoni
        'ryu',  # Central Okinawan (Ryukyuan)
        'bi',   # Bislama
        'ch',   # Chamorro
        'akz',  # Alabama
        'ff',   # Fula
    },

    'more-historical': {
        'syc',  # Classical Syriac
        'cu',   # Church Slavic
        'goh',  # Old High German
        'frm',  # Middle French
        'enm',  # Middle English
        'sga',  # Old Irish
        'pro',  # Old Provençal
        'osx',  # Old Saxon
        'got',  # Gothic
        'hbo',  # Ancient Hebrew
        'nci',  # Classical Nahuatl
        'arc',  # Aramaic (non-modern)
        'sux',  # Sumerian
        'ota',  # Ottoman Turkish
        'dum',  # Middle Dutch
        'gml',  # Middle Low German
        'gmh',  # Middle High German
        'ofs',  # Old Frisian
        'osp',  # Old Spanish
        'roa-opt',  # Old Portuguese
        'prg',  # Prussian
        'liv',  # Livonian
        'egx',  # Egyptian languages
        'akk',  # Akkadian
        'odt',  # Old Dutch
        'oge',  # Old Georgian
        'frk',  # Frankish
        'axm',  # Middle Armenian
        'txb',  # Tokharian B
        'orv',  # Old Russian
        'xto',  # Tokharian A
        'peo',  # Old Persian
        'ae',   # Avestan
        'xno',  # Anglo-Norman
        'uga',  # Ugaritic
        'mga',  # Middle Irish
        'egy',  # Ancient Egyptian
        'xpr',  # Parthian
        'cop',  # Coptic
        'hit',  # Hittite
    },

    'more-artificial': {
        'jbo',  # Lojban
        'ia',   # Interlingua
        'nov',  # Novial
        'ie',   # Interlingue
    }
}

COMMON_LANGUAGES = LANGUAGES['common'] | LANGUAGES['common-historical'] | LANGUAGES['common-artificial']
ALL_LANGUAGES = COMMON_LANGUAGES | LANGUAGES['more'] | LANGUAGES['more-historical'] | LANGUAGES['more-artificial']
HISTORICAL_LANGUAGES = LANGUAGES['common-historical'] | LANGUAGES['more-historical']

# The top languages we support, in order
CORE_LANGUAGES = ['en', 'fr', 'de', 'it', 'es', 'ru', 'pt', 'ja', 'zh', 'nl']

LANGUAGE_NAME_OVERRIDES = {
    'sh': 'Serbo-Croatian',
    'aus-x-wati': 'Western Desert'
}


def standardize_as_list(text, token_filter=None):
    """
    Get a list of tokens or stems that appear in the text.

    `token_filter` is an optional function to apply to the list of tokens,
    performing language-specific lemmatization and stopword removal. In
    practice, the only such filter is for English.

    >>> standardize_as_list('the dog', token_filter=english_filter)
    ['dog']
    >>> standardize_as_list('a big dog', token_filter=english_filter)
    ['big', 'dog']
    >>> standardize_as_list('a big dog')
    ['a', 'big', 'dog']
    >>> standardize_as_list('big dogs', token_filter=english_lemmatized_filter)
    ['big', 'dog']
    >>> standardize_as_list('BIG DOGS', token_filter=english_filter)
    ['big', 'dogs']
    >>> standardize_as_list('to go', token_filter=english_filter)
    ['go']
    >>> standardize_as_list('the', token_filter=english_filter)
    ['the']
    >>> standardize_as_list('to', token_filter=english_filter)
    ['to']
    """
    text = fix_text(text)
    tokens = [token for token in simple_tokenize(text)]
    if token_filter is not None:
        tokens = token_filter(tokens)
    return tokens


def standardize_text(text, token_filter=None):
    """
    Get a string made from the tokens in the text, joined by
    underscores. The tokens may have a language-specific `token_filter`
    applied to them. See `standardize_as_list()`.

        >>> standardize_text(' cat')
        'cat'

        >>> standardize_text('Italian supercat')
        'italian_supercat'

        >>> standardize_text('Test?!')
        'test'

        >>> standardize_text('TEST.')
        'test'

        >>> standardize_text('test/test')
        'test_test'

        >>> standardize_text('   u\N{COMBINING DIAERESIS}ber\\n')
        'über'

        >>> standardize_text('embedded' + chr(9) + 'tab')
        'embedded_tab'

        >>> standardize_text('_')
        '_'

        >>> standardize_text(',')
        ''
    """
    return '_'.join(standardize_as_list(text, token_filter))


def standardize_topic(topic):
    """
    Get a canonical representation of a Wikipedia topic, which may include
    a disambiguation string in parentheses. Returns a concept URI that
    may be disambiguated as a noun.

    >>> standardize_topic('Township (United States)')
    '/c/en/township/n/wp/united_states'
    """
    # find titles of the form Foo (bar)
    topic = topic.replace('_', ' ')
    match = re.match(r'([^(]+) \(([^)]+)\)', topic)
    if not match:
        return standardized_concept_uri('en', topic)
    else:
        return standardized_concept_uri('en', match.group(1), 'n', 'wp', match.group(2))


def standardized_concept_name(lang, text):
    """
    DEPRECATED: Use `standardize_text` instead.

    Pass the text on to `standardize_text` to get its normal form. Disregard
    the language. If you want to run text through a particular filter, pass
    that filter as the second argument to `standardize_text`.

    >>> standardized_concept_name('en', 'this is a test')
    'this_is_a_test'
    >>> standardized_concept_name('es', 'ESTO ES UNA PRUEBA')
    'esto_es_una_prueba'
    """
    return standardize_text(text, None)

normalized_concept_name = standardized_concept_name


def standardized_concept_uri(lang, text, *more):
    """
    Make the appropriate URI for a concept in a particular language, including
    stemming the text if necessary, normalizing it, and joining it into a
    concept URI.

    Items in 'more' will not be stemmed, but will go through the other
    normalization steps.

    >>> standardized_concept_uri('en', 'this is a test')
    '/c/en/this_is_test'
    >>> standardized_concept_uri('en', 'this is a test', 'n', 'example phrase')
    '/c/en/this_is_test/n/example_phrase'
    """
    lang = lang.lower()
    if lang in LCODE_ALIASES:
        lang = LCODE_ALIASES[lang]
    norm_text = standardized_concept_name(lang, text)
    more_text = [standardize_text(item) for item in more if item is not None]
    return concept_uri(lang, norm_text, *more_text)

normalized_concept_uri = standardized_concept_uri


def get_uri_language(uri):
    """
    Extract the language from a concept URI. If the URI points to an assertion,
    get the language of its first concept.
    """
    if uri.startswith('/a/'):
        return get_uri_language(parse_possible_compound_uri('a', uri)[0])
    else:
        return split_uri(uri)[1]


def valid_concept_name(text):
    """
    Returns whether this text can be reasonably represented in a concept
    URI. This helps to protect against making useless concepts out of
    empty strings or punctuation.

    >>> valid_concept_name('word')
    True
    >>> valid_concept_name('the')
    True
    >>> valid_concept_name(',,')
    False
    >>> valid_concept_name(',')
    False
    >>> valid_concept_name('/')
    False
    >>> valid_concept_name(' ')
    False
    """
    return bool(standardize_text(text))


def is_negative_relation(rel):
    return rel.startswith('/r/Not') or rel == '/r/Antonym' or rel == '/r/DistinctFrom'

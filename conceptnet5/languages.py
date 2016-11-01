# There are various cases of language codes that we want to merge or redirect
# to another language code. To promote data alignment, when there is
# uncertainty about whether multiple language codes are just variations of the
# "same language", we favor treating them as the same language.

LCODE_ALIASES = {
    # Pretend that various Chinese languages and variants are equivalent. This
    # is linguistically problematic, but it's also very helpful for aligning
    # them on terms where they actually are the same.
    #
    # This would mostly be a problem if ConceptNet was being used to *generate*
    # Chinese natural language text.
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
    # into the macrolanguage 'sh' without unifying the scripts.
    'bs': 'sh',
    'hr': 'sh',
    'sr': 'sh',
    'hbs': 'sh',
    'sr-latn': 'sh',
    'sr-cyrl': 'sh',

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
# from languages not in this list get filtered out at the point where we merge
# assertions.
#
# The main criteria are that the language should:
#
# - be involved in at least 500 edges
# - have a consistent BCP 47 language code
# - not be a sign language
#   (we don't have a good computational representation of signing)
# - have extant native speakers, be historically important, or be a
#   fully-developed artificial language

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
        'ast',  # Asturian
        'hsb',  # Upper Sorbian
        'ka',   # Georgian
        'he',   # Hebrew
        'no',   # Norwegian (Bokmål or Nynorsk)
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
        'ur',   # Urdu
        'af',   # Afrikaans
        'sa',   # Sanskrit
        'th',   # Thai
        'fil',  # Filipino
        'eu',   # Basque
        'rup',  # Aromanian
        'uk',   # Ukrainian
        'cy',   # Welsh
        'be',   # Belarusian
        'ta',   # Tamil
        'ku',   # Kurdish
        'az',   # Azerbaijani
        'kk',   # Kazakh
        'sw',   # Swahili
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
        'gv',   # Manx
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
        'frp',  # Arpitan (Franco-Provençal)
        'mi',   # Maori
        'yi',   # Yiddish
        'dsb',  # Lower Sorbian
        'vec',  # Venetian
        'ln',   # Lingala
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
        'qu',   # Quechua
        'scn',  # Sicilian
        'haw',  # Hawaiian
        'bm',   # Bambara
        'iu',   # Inuktitut
        'lo',   # Lao
        'crh',  # Crimean Turkish
        'ses',  # Koyraboro Senni
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
        'pjt',  # Pitjantjatjara (Western Desert)
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
        'bi',   # Bislama
        'ch',   # Chamorro
        'akz',  # Alabama
        'ff',   # Fula
        'xh',   # Xhosa
        'ii',   # Yi
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
        'qya',  # Quenya
    }
}

COMMON_LANGUAGES = LANGUAGES['common'] | LANGUAGES['common-historical'] | LANGUAGES['common-artificial']
ALL_LANGUAGES = COMMON_LANGUAGES | LANGUAGES['more'] | LANGUAGES['more-historical'] | LANGUAGES['more-artificial']
HISTORICAL_LANGUAGES = LANGUAGES['common-historical'] | LANGUAGES['more-historical']
RTL_LANGUAGES = {
    # Arabic script
    'ar', 'bal', 'fa', 'ku', 'ps', 'sd', 'tk', 'ug', 'ur',
    # Hebrew script
    'he', 'yi',
    # Syriac script
    'syc',
    # Thaana script
    'dv',
}

# The top languages we support, in order
CORE_LANGUAGES = ['en', 'fr', 'de', 'it', 'es', 'ru', 'pt', 'ja', 'zh', 'nl']

LANGUAGE_NAMES = {
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'es': 'Spanish',
    'ru': 'Russian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'nl': 'Dutch',
    'fi': 'Finnish',
    'pl': 'Polish',
    'bg': 'Bulgarian',
    'sv': 'Swedish',
    'cs': 'Czech',
    'sh': 'Serbo-Croatian',
    'sl': 'Slovenian',
    'ar': 'Arabic',
    'ca': 'Catalan',
    'hu': 'Hungarian',
    'se': 'Northern Sami',
    'is': 'Icelandic',
    'ro': 'Romanian',
    'el': 'Greek',
    'lv': 'Latvian',
    'ms': 'Malay / Indonesian',
    'tr': 'Turkish',
    'da': 'Danish',
    'ga': 'Irish',
    'vi': 'Vietnamese',
    'ko': 'Korean',
    'hy': 'Armenian',
    'gl': 'Galician',
    'oc': 'Occitan',
    'fo': 'Faroese',
    'gd': 'Scottish Gaelic',
    'fa': 'Persian',
    'ast': 'Asturian',
    'hsb': 'Upper Sorbian',
    'ka': 'Georgian',
    'he': 'Hebrew',
    'no': 'Norwegian',
    'sq': 'Albanian',
    'mg': 'Malagasy',
    'nrf': 'Jèrriais',
    'sk': 'Slovak',
    'lt': 'Lithuanian',
    'et': 'Estonian',
    'te': 'Telugu',
    'mk': 'Macedonian',
    'nv': 'Navajo',
    'hi': 'Hindi',
    'ur': 'Urdu',
    'af': 'Afrikaans',
    'sa': 'Sanskrit',
    'th': 'Thai',
    'fil': 'Filipino',
    'eu': 'Basque',
    'rup': 'Aromanian',
    'uk': 'Ukrainian',
    'cy': 'Welsh',
    'be': 'Belarusian',
    'ta': 'Tamil',
    'ku': 'Kurdish',
    'az': 'Azerbaijani',
    'kk': 'Kazakh',
    'sw': 'Swahili',
    'la': 'Latin',
    'grc': 'Ancient Greek',
    'xcl': 'Classical Armenian',
    'fro': 'Old French',
    'ang': 'Old English',
    'non': 'Old Norse',
    'gv': 'Manx',
    'mul': 'Multilingual',
    'eo': 'Esperanto',
    'io': 'Ido',
    'vo': 'Volapük',
    'rm': 'Romansh',
    'br': 'Breton',
    'lb': 'Luxembourgish',
    'fy': 'Western Frisian',
    'frp': 'Franco-Provençal',
    'mi': 'Maori',
    'yi': 'Yiddish',
    'dsb': 'Lower Sorbian',
    'vec': 'Venetian',
    'ln': 'Lingala',
    'fur': 'Friulian',
    'pap': 'Papiamento',
    'nds': 'Low German',
    'mn': 'Mongolian',
    'km': 'Khmer',
    'ba': 'Bashkir',
    'os': 'Ossetic',
    'sco': 'Scots',
    'lld': 'Ladin',
    'bn': 'Bengali',
    'mt': 'Maltese',
    'ady': 'Adyghe',
    'qu': 'Quechua',
    'scn': 'Sicilian',
    'haw': 'Hawaiian',
    'bm': 'Bambara',
    'iu': 'Inuktitut',
    'lo': 'Lao',
    'crh': 'Crimean Turkish',
    'ses': 'Koyraboro Senni',
    'tg': 'Tajik',
    'vep': 'Veps',
    'wa': 'Walloon',
    'kw': 'Cornish',
    'co': 'Corsican',
    'tt': 'Tatar',
    'ky': 'Kyrgyz',
    'ceb': 'Cebuano',
    'nan': 'Min Nan Chinese',
    'dlm': 'Dalmatian',
    'mdf': 'Moksha',
    'stq': 'Saterland Frisian',
    'uz': 'Uzbek',
    'pcd': 'Picard',
    'my': 'Burmese',
    'zu': 'Zulu',
    'sc': 'Sardinian',
    'tk': 'Turkmen',
    'ht': 'Haitian Creole',
    'lad': 'Ladino',
    'arn': 'Mapuche',
    'srn': 'Sranan Tongo',
    'ps': 'Pashto',
    'gu': 'Gujarati',
    'kl': 'Kalaallisut',
    'mr': 'Marathi',
    'tpi': 'Tok Pisin',
    'hil': 'Hiligaynon',
    'kn': 'Kannada',
    'ne': 'Nepali',
    'wym': 'Wymysorys',
    'ug': 'Uyghur',
    'nap': 'Neapolitan',
    'oj': 'Ojibwa',
    'mwl': 'Mirandese',
    'frr': 'Northern Frisian',
    'an': 'Aragonese',
    'yua': 'Yucateco',
    'cv': 'Chuvash',
    'bo': 'Tibetan',
    'zdj': 'Ngazidja Comorian',
    'chr': 'Cherokee',
    'sah': 'Sakha',
    'pal': 'Pahlavi',
    'ce': 'Chechen',
    'wo': 'Wolof',
    'li': 'Limburgish',
    'ml': 'Malayalam',
    'egl': 'Emilian',
    'csb': 'Kashubian',
    'ist': 'Istriot',
    'lkt': 'Lakota',
    'pi': 'Pali',
    'kbd': 'Kabardian',
    'twf': 'Northern Tiwa',
    'jv': 'Javanese',
    'fon': 'Fon',
    'nah': 'Nahuatl languages',
    'pa': 'Punjabi',
    'myv': 'Erzya',
    'nmn': '!Xóõ',
    'rom': 'Romany',
    'ltg': 'Latgalian',
    'ee': 'Ewe',
    'sm': 'Samoan',
    'am': 'Amharic',
    'kum': 'Kumyk',
    'krc': 'Karachay-Balkar',
    'gsw': 'Swiss German',
    'dak': 'Dakota',
    'swb': 'Comorian',
    'bal': 'Baluchi',
    'si': 'Sinhala',
    'so': 'Somali',
    'su': 'Sundanese',
    'kjh': 'Khakas',
    'cic': 'Chickasaw',
    'gag': 'Gagauz',
    'nog': 'Nogai',
    'chk': 'Chuukese',
    'ha': 'Hausa',
    'tyv': 'Tuvinian',
    'nhn': 'Central Nahuatl',
    'zza': 'Zaza',
    'oma': 'Omaha-Ponca',
    'vot': 'Votic',
    'krl': 'Karelian',
    'rw': 'Kinyarwanda',
    'aa': 'Afar',
    'or': 'Oriya',
    'alt': 'Southern Altai',
    'esu': 'Central Yupik',
    'ccc': 'Chamicuro',
    'ab': 'Abkhazian',
    'ppl': 'Pipil',
    'chl': 'Cahuilla',
    'ain': 'Ainu',
    'na': 'Nauru',
    'ty': 'Tahitian',
    'wau': 'Waurá',
    'dua': 'Duala',
    'rap': 'Rapa Nui',
    'adx': 'Amdo Tibetan',
    'cjs': 'Shor',
    'tet': 'Tetum',
    'kim': 'Tofa',
    'hak': 'Hakka',
    'lij': 'Ligurian',
    'gn': 'Guarani',
    'tpw': 'Tupi',
    'sms': 'Skolt Sami',
    'xmf': 'Mingrelian',
    'smn': 'Inari Sami',
    'raj': 'Rajasthani',
    'cim': 'Cimbrian',
    'rue': 'Rusyn',
    'hke': 'Hunde',
    'fj': 'Fijian',
    'pms': 'Piedmontese',
    'wae': 'Walser',
    'yo': 'Yoruba',
    'mh': 'Marshallese',
    'szl': 'Silesian',
    'pjt': 'Pitjantjatjara',
    'khb': 'Tai Lü',
    'dv': 'Divehi',
    'udm': 'Udmurt',
    'dje': 'Zarma',
    'ilo': 'Ilocano',
    'aii': 'Assyrian Neo-Aramaic',
    'koy': 'Koyukon',
    'war': 'Waray',
    'lmo': 'Lombard',
    'ti': 'Tigrinya',
    'av': 'Avar',
    'mch': 'Maquiritari',
    'abe': 'Western Abenaki',
    'cho': 'Choctaw',
    'xwo': 'Oirat',
    'za': 'Zhuang',
    'ki': 'Kikuyu',
    'lzz': 'Laz',
    'sd': 'Sindhi',
    'st': 'Sotho',
    'shh': 'Shoshoni',
    'bi': 'Bislama',
    'ch': 'Chamorro',
    'akz': 'Alabama',
    'ff': 'Fula',
    'xh': 'Xhosa',
    'ii': 'Yi',
    'syc': 'Classical Syriac',
    'cu': 'Church Slavic',
    'goh': 'Old High German',
    'frm': 'Middle French',
    'enm': 'Middle English',
    'sga': 'Old Irish',
    'pro': 'Old Provençal',
    'osx': 'Old Saxon',
    'got': 'Gothic',
    'hbo': 'Ancient Hebrew',
    'nci': 'Classical Nahuatl',
    'arc': 'Aramaic',
    'sux': 'Sumerian',
    'ota': 'Ottoman Turkish',
    'dum': 'Middle Dutch',
    'gml': 'Middle Low German',
    'gmh': 'Middle High German',
    'ofs': 'Old Frisian',
    'osp': 'Old Spanish',
    'roa-opt': 'Old Portuguese',
    'prg': 'Prussian',
    'liv': 'Livonian',
    'egx': 'Egyptian languages',
    'akk': 'Akkadian',
    'odt': 'Old Dutch',
    'oge': 'Old Georgian',
    'frk': 'Frankish',
    'axm': 'Middle Armenian',
    'txb': 'Tokharian B',
    'orv': 'Old Russian',
    'xto': 'Tokharian A',
    'peo': 'Old Persian',
    'ae': 'Avestan',
    'xno': 'Anglo-Norman',
    'uga': 'Ugaritic',
    'mga': 'Middle Irish',
    'egy': 'Ancient Egyptian',
    'xpr': 'Parthian',
    'cop': 'Coptic',
    'hit': 'Hittite',
    'jbo': 'Lojban',
    'ia': 'Interlingua',
    'nov': 'Novial',
    'ie': 'Interlingue',
    'qya': 'Quenya',
}


def get_language_name(code):
    """
    Get the English name of a language ConceptNet supports.
    """
    if code in LCODE_ALIASES:
        code = LCODE_ALIASES['code']
    return LANGUAGE_NAMES.get(code, code)

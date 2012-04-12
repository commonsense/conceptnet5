#!/usr/bin/env python
# -*- coding: utf-8 -*-


__all__ = ['langs']


class LangDb(dict):
    """A customized dict in which ISO 639-1 language codes are mapped to their
    English and native language names.

    By default, language codes are mapped to their primary native language
    names (i.e., if you use normal dict methods, you'll be dealing with native
    language names).

    English names for languages and alternative names (if applicable) are also
    accessible via special methods.

    Some examples (with dummy data):

    >>> langs = LangDb({
    ... u'en': (u'English', u'English'),
    ... u'de': (u'German', u'Deutsche'),
    ... u'fr': (u'French', (u'français',u'langue française')),
    ... u'gd': ((u'Scottish Gaelic',u'Gaelic'), u'Gàidhlig'),
    ... })
    >>> langs
    <LangDb: 4 langs>

    # Accessing by key returns primary native name
    >>> langs['en']
    u'English'
    >>> langs['fr']
    u'français'
    >>> langs['gd']
    u'Gàidhlig'
    >>> langs['de']
    u'Deutsche'

    # All the normal dict protocol methods are there, and they all deal
    # with primary native names.
    >>> langs.get('en')
    u'English'
    >>> langs.get('fr')
    u'français'
    >>> sorted(langs.items())
    [(u'de', u'Deutsche'), (u'en', u'English'), (u'fr', u'français'), (u'gd', u'Gàidhlig')]
    >>> sorted(langs.keys())
    [u'de', u'en', u'fr', u'gd']
    >>> sorted(langs.values())
    [u'Deutsche', u'English', u'Gàidhlig', u'français']

    # You can also explicitly ask for the native name
    >>> langs.native_name('en')
    u'English'
    >>> langs.native_name('fr')
    u'français'

    # Asking for all names will always return a tuple, even if there is
    # only one name
    >>> langs.native_name('fr', all_names=True)
    (u'français', u'langue français')
    >>> langs.native_name('de', all_names=True)
    (u'Deutsche',)

    >>> langs.english_name('fr')
    u'French'
    >>> langs.english_name('gd')
    u'Scottish Gaelic'
    >>> langs.english_name('gd', all_names=True)
    (u'Scottish Gaelic', u'Gaelic')

    # And access iterators over the available language codes or names
    # (these are basically synonyms for iterkeys() and itervalues()
    >>> sorted(langs.codes)
    [u'de', u'en', u'fr', u'gd']
    >>> sorted(langs.names)
    [u'Deutsche', u'English', u'Gàidhlig', u'français']
    """

    ENGLISH = 0
    NATIVE = 1

    # Normal dict protocol
    def __getitem__(self, key):
        """By default, accessing the db by language code will return the
        native language name."""
        english, native = super(LangDb, self).__getitem__(key)
        return native if isinstance(native, basestring) else native[0]

    def get(self, *args, **kwargs):
        value = super(LangDb, self).get(*args, **kwargs)
        try:
            english, native = value
            return primary(native)
        except TypeError:
            return value

    def iteritems(self):
        """An iterator over (code, primary native name) pairs."""
        for code, (english, native) in super(LangDb, self).iteritems():
            yield code, primary(native)

    def items(self):
        """A list of (code, primary native name) pairs."""
        return list(self.iteritems())

    def itervalues(self):
        return (primary(native) for english, native
                in super(LangDb, self).itervalues())

    def values(self):
        return list(self.itervalues())

    # Special LangDb properties and methods
    @property
    def codes(self):
        """An iterator over the language codes in the database."""
        return self.iterkeys()

    @property
    def names(self):
        """An iterator over the primary native names for the languages in the
        database."""
        return self.itervalues()

    @property
    def native_names(self):
        """An iterator over (code, native name) pairs."""
        for code, (english, native) in super(LangDb, self).iteritems():
            yield code, primary(native)

    @property
    def english_names(self):
        """An iterator over (code, English name) pairs."""
        for code, (english, native) in super(LangDb, self).iteritems():
            yield code, primary(english)

    def native_name(self, code, all_names=False):
        """Returns the native name for the given language code.  If all_names
        is True, returns a tuple of all the possible native names."""
        return self._some_name(code, self.NATIVE, all_names)

    def english_name(self, code, all_names=False):
        """Returns the English name for the given language code. If all_names
        is True, returns a tuple of all the possible English names."""
        return self._some_name(code, self.ENGLISH, all_names)

    def _some_name(self, code, which, all_names):
        """Utility function to pull an English or native name (or all names)
        from the db by language code.  Used by native_name() and
        english_name()."""
        value = super(LangDb, self).__getitem__(code)
        if value is None:
            raise KeyError, code
        name = value[which]
        if not all_names:
            return primary(name)
        else:
            return name if isinstance(name, tuple) else (name,)

    def raw_data(self):
        """Provide access to a copy of the raw underlying data."""
        return dict(super(LangDb, self).iteritems())

    def __repr__(self):
        return '<LangDb: %d langs>' % len(self)


def primary(names):
    """Returns the primary name from names, which can be a string or a tuple
    of strings.  If it's a string, it is returned.  If it's a tuple, the first
    element is returned.

    >>> primary('French')
    'French'
    >>> primary(('Alpha', 'Beta'))
    'Alpha'

    >>> primary('Alpha')
    'Alpha'
    >>> primary(('Alpha', 'Beta'))
    'Alpha'
    >>> primary(None)
    Traceback (most recent call last):
    ...
    TypeError: 'NoneType' object is unsubscriptable
    """
    return names if isinstance(names, basestring) else names[0]


# Maps two-letter language codes to (english name, native name) tuples, where
# either name may be a single string or a list of strings.
langs = LangDb({
    u'aa': (u'Afar', u'Afaraf'),
    u'ab': (u'Abkhaz', u'Аҧсуа'),
    u'ae': (u'Avestan', u'avesta'),
    u'af': (u'Afrikaans', u'Afrikaans'),
    u'ak': (u'Akan', u'Akan'),
    u'am': (u'Amharic', u'አማርኛ'),
    u'an': (u'Aragonese', u'Aragonés'),
    u'ar': (u'Arabic', u'العربية'),
    u'as': (u'Assamese', u'অসমীয়া'),
    u'av': (u'Avaric', (u'авар мацӀ',u'магӀарул мацӀ')),
    u'ay': (u'Aymara', u'aymar aru'),
    u'az': (u'Azerbaijani', u'azərbaycan dili'),
    u'ba': (u'Bashkir', u'башҡорт теле'),
    u'be': (u'Belarusian', u'Беларуская'),
    u'bg': (u'Bulgarian', u'български език'),
    u'bh': (u'Bihari', u'भोजपुरी'),
    u'bi': (u'Bislama', u'Bislama'),
    u'bm': (u'Bambara', u'bamanankan'),
    u'bn': (u'Bengali', u'বাংলা'),
    u'bo': ((u'Tibetan Standard',u'Tibetan',u'Central'), u'བོད་ཡིག'),
    u'br': (u'Breton', u'brezhoneg'),
    u'bs': (u'Bosnian', u'bosanski jezik'),
    u'ca': ((u'Catalan',u' Valencian'), u'Català'),
    u'ce': (u'Chechen', u'нохчийн мотт'),
    u'ch': (u'Chamorro', u'Chamoru'),
    u'co': (u'Corsican', (u'corsu',u'lingua corsa')),
    u'cr': (u'Cree', u'ᓀᐦᐃᔭᐍᐏᐣ'),
    u'cs': (u'Czech', (u'česky',u'čeština')),
    u'cu': ((u'Old Church Slavonic',
             u'Church Slavic',
             u'Church Slavonic',
             u'Old Bulgarian',
             u'Old Slavonic'),
            u'ѩзыкъ словѣньскъ'),
    u'cv': (u'Chuvash', u'чӑваш чӗлхи'),
    u'cy': (u'Welsh', u'Cymraeg'),
    u'da': (u'Danish', u'dansk'),
    u'de': (u'German', u'Deutsch'),
    u'dv': ((u'Divehi',u' Dhivehi',u' Maldivian',u''), u'ދިވެހި'),
    u'dz': (u'Dzongkha', u'རྫོང་ཁ'),
    u'ee': (u'Ewe', u'Eʋegbe'),
    u'el': (u'Greek', u'Ελληνικά'),
    u'en': (u'English', u'English'),
    u'eo': (u'Esperanto', u'Esperanto'),
    u'es': ((u'Spanish',u' Castilian'), (u'español',u'castellano')),
    u'et': (u'Estonian', (u'eesti',u'eesti keel')),
    u'eu': (u'Basque', (u'euskara',u'euskera')),
    u'fa': (u'Persian', u'فارسی'),
    u'ff': ((u'Fula',u' Fulah',u' Pulaar',u' Pular'),
            (u'Fulfulde',u'Pulaar',u'Pular')),
    u'fi': (u'Finnish', (u'suomi',u'suomen kieli')),
    u'fj': (u'Fijian', u'vosa Vakaviti'),
    u'fo': (u'Faroese', u'føroyskt'),
    u'fr': (u'French', (u'français',u'langue française')),
    u'fy': (u'Western Frisian', u'Frysk'),
    u'ga': (u'Irish', u'Gaeilge'),
    u'gd': ((u'Scottish Gaelic',u'Gaelic'), u'Gàidhlig'),
    u'gl': (u'Galician', u'Galego'),
    u'gn': (u'Guaraní', u"Avañe'ẽ"),
    u'gu': (u'Gujarati', u'ગુજરાતી'),
    u'gv': (u'Manx', (u'Gaelg',u'Gailck')),
    u'ha': (u'Hausa', (u'Hausa',u'هَوُسَ')),
    u'he': (u'Hebrew ', u'עברית'),
    u'hi': (u'Hindi', (u'हिन्दी',u'हिंदी')),
    u'ho': (u'Hiri Motu', u'Hiri Motu'),
    u'hr': (u'Croatian', u'hrvatski'),
    u'ht': ((u'Haitian',u' Haitian Creole'), u'Kreyòl ayisyen'),
    u'hu': (u'Hungarian', u'Magyar'),
    u'hy': (u'Armenian', u'Հայերեն'),
    u'hz': (u'Herero', u'Otjiherero'),
    u'ia': (u'Interlingua', u'Interlingua'),
    u'id': (u'Indonesian', u'Bahasa Indonesia'),
    u'ie': (u'Interlingue', (u'Occidental',u'Interlingue')),
    u'ig': (u'Igbo', u'Asụsụ Igbo'),
    u'ii': (u'Nuosu', u'ꆈꌠ꒿ Nuosuhxop'),
    u'ik': (u'Inupiaq', (u'Iñupiaq',u'Iñupiatun')),
    u'io': (u'Ido', u'Ido'),
    u'is': (u'Icelandic', u'Íslenska'),
    u'it': (u'Italian', u'Italiano'),
    u'iu': (u'Inuktitut', u'ᐃᓄᒃᑎᑐᑦ'),
    u'ja': (u'Japanese', u'日本語 '),
    u'jv': (u'Javanese', u'basa Jawa'),
    u'ka': (u'Georgian', u'ქართული'),
    u'kg': (u'Kongo', u'KiKongo'),
    u'ki': ((u'Kikuyu',u'Gikuyu'), u'Gĩkũyũ'),
    u'kj': ((u'Kwanyama',u'Kuanyama'), u'Kuanyama'),
    u'kk': (u'Kazakh', u'Қазақ тілі'),
    u'kl': ((u'Kalaallisut',u'Greenlandic'),
            (u'kalaallisut',u'kalaallit oqaasii')),
    u'km': (u'Khmer', u'ភាសាខ្មែរ'),
    u'kn': (u'Kannada', u'ಕನ್ನಡ'),
    u'ko': (u'Korean', (u'한국어 ',u'조선말 ')),
    u'kr': (u'Kanuri', u'Kanuri'),
    u'ks': (u'Kashmiri', (u'कश्मीरी',u'كشميري‎')),
    u'ku': (u'Kurdish', (u'Kurdî',u'كوردی‎')),
    u'kv': (u'Komi', u'коми кыв'),
    u'kw': (u'Cornish', u'Kernewek'),
    u'ky': ((u'Kirghiz',u'Kyrgyz'), u'кыргыз тили'),
    u'la': (u'Latin', (u'latine',u'lingua latina')),
    u'lb': ((u'Luxembourgish',u'Letzeburgesch'), u'Lëtzebuergesch'),
    u'lg': (u'Luganda', u'Luganda'),
    u'li': ((u'Limburgish',u'Limburgan',u'Limburger'), u'Limburgs'),
    u'ln': (u'Lingala', u'Lingála'),
    u'lo': (u'Lao', u'ພາສາລາວ'),
    u'lt': (u'Lithuanian', u'lietuvių kalba'),
    u'lu': (u'Luba-Katanga', u'Luba-Katanga'),
    u'lv': (u'Latvian', u'latviešu valoda'),
    u'mg': (u'Malagasy', u'Malagasy fiteny'),
    u'mh': (u'Marshallese', u'Kajin M̧ajeļ'),
    u'mi': (u'Māori', u'te reo Māori'),
    u'mk': (u'Macedonian', u'македонски јазик'),
    u'ml': (u'Malayalam', u'മലയാളം'),
    u'mn': (u'Mongolian', u'Монгол'),
    u'mr': (u'Marathi', u'मराठी'),
    u'ms': (u'Malay', (u'bahasa Melayu',u'بهاس ملايو‎')),
    u'mt': (u'Maltese', u'Malti'),
    u'my': (u'Burmese', u'ဗမာစာ'),
    u'na': (u'Nauru', u'Ekakairũ Naoero'),
    u'nb': (u'Norwegian Bokmål', u'Norsk bokmål'),
    u'nd': (u'North Ndebele', u'isiNdebele'),
    u'ne': (u'Nepali', u'नेपाली'),
    u'ng': (u'Ndonga', u'Owambo'),
    u'nl': (u'Dutch', (u'Nederlands',u'Vlaams')),
    u'nn': (u'Norwegian Nynorsk', u'Norsk nynorsk'),
    u'no': (u'Norwegian', u'Norsk'),
    u'nr': (u'South Ndebele', u'isiNdebele'),
    u'nv': ((u'Navajo',u'Navaho'), (u'Diné bizaad',u'Dinékʼehǰí')),
    u'ny': ((u'Chichewa',u' Chewa',u' Nyanja'), (u'chiCheŵa',u'chinyanja')),
    u'oc': (u'Occitan ', u'Occitan'),
    u'oj': (u'Ojibwa', u'ᐊᓂᔑᓈᐯᒧᐎᓐ'),
    u'om': (u'Oromo', u'Afaan Oromoo'),
    u'or': (u'Oriya', u'ଓଡ଼ିଆ'),
    u'os': ((u'Ossetian',u'Ossetic'), u'Ирон æвзаг'),
    u'pa': ((u'Panjabi',u'Punjabi'), (u'ਪੰਜਾਬੀ',u'پنجابی‎')),
    u'pi': (u'Pāli', u'पाऴि'),
    u'pl': (u'Polish', u'polski'),
    u'ps': ((u'Pashto',u'Pushto'), u'پښتو'),
    u'pt': (u'Portuguese', u'Português'),
    u'qu': (u'Quechua', (u'Runa Simi',u'Kichwa')),
    u'rm': (u'Romansh', u'rumantsch grischun'),
    u'rn': (u'Kirundi', u'kiRundi'),
    u'ro': ((u'Romanian',u'Moldavian',u'Moldovan'), u'română'),
    u'ru': (u'Russian', u'Русский язык'),
    u'rw': (u'Kinyarwanda', u'Ikinyarwanda'),
    u'sa': (u'Sanskrit', u'संस्कृतम्'),
    u'sc': (u'Sardinian', u'sardu'),
    u'sd': (u'Sindhi', (u'सिन्धी',u'سنڌي، سندھی‎')),
    u'se': (u'Northern Sami', u'Davvisámegiella'),
    u'sg': (u'Sango', u'yângâ tî sängö'),
    u'si': ((u'Sinhala',u'Sinhalese'), u'සිංහල'),
    u'sk': (u'Slovak', u'slovenčina'),
    u'sl': (u'Slovene', u'slovenščina'),
    u'sm': (u'Samoan', u"gagana fa'a Samoa"),
    u'sn': (u'Shona', u'chiShona'),
    u'so': (u'Somali', (u'Soomaaliga',u'af Soomaali')),
    u'sq': (u'Albanian', u'Shqip'),
    u'sr': (u'Serbian', u'српски језик'),
    u'ss': (u'Swati', u'SiSwati'),
    u'st': (u'Southern Sotho', u'Sesotho'),
    u'su': (u'Sundanese', u'Basa Sunda'),
    u'sv': (u'Swedish', u'svenska'),
    u'sw': (u'Swahili', u'Kiswahili'),
    u'ta': (u'Tamil', u'தமிழ்'),
    u'te': (u'Telugu', u'తెలుగు'),
    u'tg': (u'Tajik', (u'тоҷикӣ',u'toğikī',u'تاجیکی‎')),
    u'th': (u'Thai', u'ไทย'),
    u'ti': (u'Tigrinya', u'ትግርኛ'),
    u'tk': (u'Turkmen', (u'Türkmen',u'Түркмен')),
    u'tl': (u'Tagalog', (u'Wikang Tagalog',u'ᜏᜒᜃᜅ᜔ ᜆᜄᜎᜓᜄ᜔')),
    u'tn': (u'Tswana', u'Setswana'),
    u'to': (u'Tonga ', u'faka Tonga'),
    u'tr': (u'Turkish', u'Türkçe'),
    u'ts': (u'Tsonga', u'Xitsonga'),
    u'tt': (u'Tatar', (u'татарча',u'tatarça',u'تاتارچا‎')),
    u'tw': (u'Twi', u'Twi'),
    u'ty': (u'Tahitian', u'Reo Mā`ohi'),
    u'ug': ((u'Uighur',u'Uyghur'), (u'Uyƣurqə',u'ئۇيغۇرچە‎')),
    u'uk': (u'Ukrainian', u'Українська'),
    u'ur': (u'Urdu', u'اردو'),
    u'uz': (u'Uzbek', (u"O'zbek',u'Ўзбек',u'أۇزبېك‎")),
    u've': (u'Venda', u'Tshivenḓa'),
    u'vi': (u'Vietnamese', u'Tiếng Việt'),
    u'vo': (u'Volapük', u'Volapük'),
    u'wa': (u'Walloon', u'Walon'),
    u'wo': (u'Wolof', u'Wollof'),
    u'xh': (u'Xhosa', u'isiXhosa'),
    u'yi': (u'Yiddish', u'ייִדיש'),
    u'yo': (u'Yoruba', u'Yorùbá'),
    u'za': ((u'Zhuang',u'Chuang'), (u'Saɯ cueŋƅ',u'Saw cuengh')),
    u'zh': (u'Chinese', (u'中文 ',u'汉语',u'漢語')),
    u'zu': (u'Zulu', u'isiZulu'),
    u'min': (u'Min Nan', u'Min Nan'),
    u'sco': (u'Scottish Gaelic', u'Scottish Gaelic'),
    u'jbo': (u'Lojban', u'lojban'),
    u'ase': (u'American Sign Language', u'American Sign Language')
})


if __name__ == '__main__':
    import doctest
    doctest.testmod()

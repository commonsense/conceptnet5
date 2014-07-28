from nose.tools import eq_

from conceptnet5.wiktparse.rules import (
    EdgeInfo, EnWiktionarySemantics, DeWiktionarySemantics
)

# Global variable to hold the parsers for the different languages
PARSERS = {
    'en': EnWiktionarySemantics('en'),
    'de': DeWiktionarySemantics('de')
}


def check_output(lang, rule_name, text, expected):
    """Callable used by all the test generators below; `text` is the string to
    be parsed; `expected` is the result the parser is expected to produce from
    the string."""
    match_list = PARSERS[lang].parse(text, rule_name)
    eq_(expected, match_list)


def test_en_etymology():
    test_list = [
        ('{{compound|blow|fish}}',
         [EdgeInfo('en', 'blow', None, 'DerivedFrom'),
          EdgeInfo('en', 'fish', None, 'DerivedFrom')]),
        ('{{etycomp|blow|fish}}',
         [EdgeInfo('en', 'blow', None, 'EtymologicallyDerivedFrom'),
          EdgeInfo('en', 'fish', None, 'EtymologicallyDerivedFrom')])
    ]
    for (text, expected) in test_list:
        yield check_output, 'en', 'etymology_section', text, expected


def test_de_sense_num():
    test_list = [
        ('1', ['1']),
        # a range of numbers is expanded to all its members
        ('1, 4-6', ['1', '4', '5', '6'])
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'sense_num', text, expected


def test_de_from_german():
    test_list = [
        # Translation template with missing target
        ('*{{fr}}: [1] {{Ü|fr|}}', []),
        # Simple template with one target
        ('*{{en}}: [1] {{Ü|en|nice}}',
         [EdgeInfo('en', 'nice', '1', 'TranslationOf')]),
        # More complicated entry with three translation in two senses
        ('*{{ru}}: [1] {{Üxx|ru|míly|милый}}; [2] {{Üxx|ru|rodnój|родной}}, {{Üxx|ru|dorogój|дорогой}}',
         [EdgeInfo('ru', 'милый', '1', 'TranslationOf'),
          EdgeInfo('ru', 'родной', '2', 'TranslationOf'),
          EdgeInfo('ru', 'дорогой', '2', 'TranslationOf')])
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'from_german', text, expected


def test_de_to_german():
    test_list = [
        (':{{Übersetzungen umleiten|5a|Ordensgemeinschaft|}} {{f}}',
         [EdgeInfo('de', 'Ordensgemeinschaft', '5a', 'TranslationOf')])
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'to_german', text, expected


def test_de_translation_section():
    """ A combination of entries in both directions (to and from German), with
    the internal table markup present."""
    test_list = [
        ("""{{Ü-Tabelle|Ü-links=
:{{Übersetzungen umleiten|5a|Ordensgemeinschaft|}} {{f}}
:{{Übersetzungen umleiten|6|Ordnung|2}} {{f}}
*{{fr}}: [1] {{Ü|fr|}}
*{{en}}: [1] {{Ü|en|nice}}; [2] {{Ü|en|dear}}
*{{fr}}: [1] {{Ü|fr|gentil}}; [2] {{Ü|fr|cher}}
*{{ja}}: [1] {{Üxx|ja|やさしい, yasashii|優しい}}; [2] {{Üxx|ja|こいしい, koishii|恋しい}}
*{{pt}}: [1] {{Ü|pt|gentil}}; [2] {{Ü|pt|querido}} {{m}}
*{{ru}}: [1] {{Üxx|ru|míly|милый}}; [2] {{Üxx|ru|rodnój|родной}}, {{Üxx|ru|dorogój|дорогой}}
|Ü-rechts=
*{{sv}}: [1] {{Ü|sv|snäll}}, {{Ü|sv|rar}}, {{Ü|sv|älsvärd}}; [2] {{Ü|sv|älskad}}, {{Ü|sv|kär}}
*{{es}}: [1, 2] {{Ü|es|amable}}, {{Ü|es|querido}}, {{Ü|es|agradable}}
*{{cs}}: [1] {{Ü|cs|milý}}, [2] {{Ü|cs|drahý}}
*{{hu}}: [1] {{Ü|hu|kedves}}
}}""",
         [EdgeInfo('de', 'Ordensgemeinschaft', '5a', 'TranslationOf'),
          EdgeInfo('de', 'Ordnung (2)', '6', 'TranslationOf'),
          EdgeInfo('en', 'nice', '1', 'TranslationOf'),
          EdgeInfo('en', 'dear', '2', 'TranslationOf'),
          EdgeInfo('fr', 'gentil', '1', 'TranslationOf'),
          EdgeInfo('fr', 'cher', '2', 'TranslationOf'),
          EdgeInfo('ja', '優しい', '1', 'TranslationOf'),
          EdgeInfo('ja', '恋しい', '2', 'TranslationOf'),
          EdgeInfo('pt', 'gentil', '1', 'TranslationOf'),
          EdgeInfo('pt', 'querido', '2', 'TranslationOf'),
          EdgeInfo('ru', 'милый', '1', 'TranslationOf'),
          EdgeInfo('ru', 'родной', '2', 'TranslationOf'),
          EdgeInfo('ru', 'дорогой', '2', 'TranslationOf'),
          EdgeInfo('sv', 'snäll', '1', 'TranslationOf'),
          EdgeInfo('sv', 'rar', '1', 'TranslationOf'),
          EdgeInfo('sv', 'älsvärd', '1', 'TranslationOf'),
          EdgeInfo('sv', 'älskad', '2', 'TranslationOf'),
          EdgeInfo('sv', 'kär', '2', 'TranslationOf'),
          EdgeInfo('es', 'amable', '1', 'TranslationOf'),
          EdgeInfo('es', 'amable', '2', 'TranslationOf'),
          EdgeInfo('es', 'querido', '1', 'TranslationOf'),
          EdgeInfo('es', 'querido', '2', 'TranslationOf'),
          EdgeInfo('es', 'agradable', '1', 'TranslationOf'),
          EdgeInfo('es', 'agradable', '2', 'TranslationOf'),
          EdgeInfo('cs', 'milý', '1', 'TranslationOf'),
          EdgeInfo('cs', 'drahý', '2', 'TranslationOf'),
          EdgeInfo('hu', 'kedves', '1', 'TranslationOf')])
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'translation_section', text, expected


def test_de_pseudo_link():
    # Strings that look like links but are really grammar and usage directives
    test_list = [
        ("''[[Zoologie]]:''", None), ("''mit [[Lokativ]]:''", None)
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'pseudo_link', text, expected


def test_de_definition():
    # Note
    test_list = [
        # Simple entry with pseudo-link (must yield empty lst)
        (":[1] ''[[Zoologie]]:'' Aal\n", []),
        # Simple entry with a single link
        (':[1] [[sprechen]]\n', [EdgeInfo('de', 'sprechen', None, None)]),
        # Simple entry with two links
        (':[1] [[Panorama]] {{n}}, [[Aussicht]] {{f}}\n',
         [EdgeInfo('de', 'Panorama', None, None),
          EdgeInfo('de', 'Aussicht', None, None)]),
        # Complex entry with usage directives and 6 actual links
        (""":[2] ''militärisch:''
::— ''(abstrakt: Militär-Gruppierung, Legion)'' [[Glied]], [[Zenturie]], [[Abteilung]], [[Abteilungsglied]], [[Kompanie]]
::— ''(personifiziert)'' der [[Hauptmann]] selbst
""",
         [EdgeInfo('de', 'Glied', None, None),
          EdgeInfo('de', 'Zenturie', None, None),
          EdgeInfo('de', 'Abteilung', None, None),
          EdgeInfo('de', 'Abteilungsglied', None, None),
          EdgeInfo('de', 'Kompanie', None, None),
          EdgeInfo('de', 'Hauptmann', None, None)])
    ]
    for (text, expected) in test_list:
        yield check_output, 'de', 'definition_section', text, expected

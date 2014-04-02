# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
This Wiktionary reader should be refactored, but it does the job for now.
"""

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
from conceptnet5.uri import Licenses, BAD_NAMES_FOR_THINGS
from conceptnet5.nodes import normalized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.json_stream import JSONStreamWriter
from conceptnet5.util.language_codes import CODE_TO_ENGLISH_NAME
import unicodedata
import re


def ascii_enough(text):
    """
    Test whether text is entirely in the ASCII set. We use this as a very rough
    way to figure out definitions that are supposed to be in English but
    aren't.
    """
    # cheap assumption: if it's ASCII, and it's meant to be in English, it's
    # probably actually in English.
    return text.encode('ascii', 'replace') == text.encode('ascii', 'ignore')


def term_is_bad(term):
    return (term in BAD_NAMES_FOR_THINGS or 'Wik' in term or ':' in term)


PARTS_OF_SPEECH = {
    'Noun': 'n',
    'Verb': 'v',
    'Adjective': 'a',
    'Adverb': 'r',
    'Preposition': 'p',
    'Pronoun': 'n',
    'Determiner': 'd',
    'Article': 'd',
    'Interjection': 'i',
    'Conjunction': 'c',
}
LANGUAGE_HEADER = re.compile(r'==\s*(.+)\s*==')
TRANS_TOP = re.compile(r"\{\{trans-top\|(.+)\}\}")
TRANS_TAG = re.compile(r"\{\{t.?\|([^|}]+)\|([^|}]+)")
CHINESE_TAG = re.compile(r"\{\{cmn-(noun|verb)+\|(s|t|st|ts)\|")
WIKILINK = re.compile(r"\[\[([^|\]#]+)")

LANGUAGES = {
    'English': 'en',

    'Afrikaans': 'af',
    'Arabic': 'ar',
    'Armenian': 'hy',
    'Basque': 'eu',
    'Belarusian': 'be',
    'Bengali': 'bn',
    'Bosnian': 'bs',
    'Bulgarian': 'bg',
    'Burmese': 'my',
    'Chinese': 'zh',
    'Crimean Tatar': 'crh',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Finnish': 'fi',
    'French': 'fr',
    'Galician': 'gl',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Icelandic': 'is',
    'Ido': 'io',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Kannada': 'kn',
    'Kazakh': 'kk',
    'Khmer': 'km',
    'Korean': 'ko',
    'Kyrgyz': 'ky',
    'Lao': 'lo',
    'Latin': 'la',
    'Lithuanian': 'lt',
    'Lojban': 'jbo',
    'Macedonian': 'mk',
    'Min Nan': 'nan',
    'Malagasy': 'mg',
    'Mandarin': 'zh',
    'Norwegian': 'no',
    'Pashto': 'ps',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Sanskrit': 'sa',
    'Sinhalese': 'si',
    'Scots': 'sco',
    'Scottish Gaelic': 'gd',
    'Serbian': 'sr',
    'Slovak': 'sk',
    'Slovene': 'sl',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swahili': 'sw',
    'Swedish': 'sv',
    'Tajik': 'tg',
    'Tamil': 'ta',
    'Thai': 'th',
    'Turkish': 'tr',
    'Turkmen': 'tk',
    'Ukrainian': 'uk',
    'Urdu': 'ur',
    'Uzbek': 'uz',
    'Vietnamese': 'vi',
    '英語': 'en',
    '日本語': 'ja'
}

SOURCE = '/s/web/en.wiktionary.org'
INTERLINGUAL = '/s/rule/wiktionary_interlingual_definitions'
MONOLINGUAL = '/s/rule/wiktionary_monolingual_definitions'
TRANSLATE = '/s/rule/wiktionary_translation_tables'
DEFINE = '/s/rule/wiktionary_define_senses'

class FindTranslations(ContentHandler):
    def __init__(self, output_file='wiktionary.json'):
        self.lang = None
        self.langcode = None
        self.inArticle = False
        self.inTitle = False
        self.curSense = None
        self.curTitle = ''
        self.curText = ''
        self.locales = []
        self.curRelation = None
        self.writer = JSONStreamWriter(output_file)

    def startElement(self, name, attrs):
        if name == 'page':
            self.inArticle = True
            self.curText = []
        elif name == 'title':
            self.inTitle = True
            self.curTitle = ''

    def endElement(self, name):
        if name == 'page':
            self.inArticle = False
            self.handleArticle(self.curTitle, ''.join(self.curText))
        elif name == 'title':
            self.inTitle = False

    def characters(self, text):
        if self.inTitle:
            self.curTitle += text
        elif self.inArticle:
            self.curText.append(text)
            if len(self.curText) > 10000:
                # bail out
                self.inArticle = False

    def handleArticle(self, title, text):
        lines = text.split('\n')
        self.pos = None
        for line in lines:
            self.handleLine(title, line.strip())

    def handleLine(self, title, line):
        language_match = LANGUAGE_HEADER.match(line)
        trans_top_match = TRANS_TOP.match(line)
        trans_tag_match = TRANS_TAG.search(line)
        chinese_match = CHINESE_TAG.search(line)
        if line.startswith('===') and line.endswith('==='):
            pos = line.strip('= ')
            if pos == 'Synonyms':
                self.curRelation = 'Synonym'
            elif pos == 'Antonym':
                self.curRelation = 'Antonym'
            elif pos == 'Related terms':
                self.curRelation = 'RelatedTo'
            elif pos == 'Derived terms':
                if not line.startswith('===='):
                    # this is at the same level as the part of speech;
                    # now we don't know what POS these apply to
                    self.pos = None
                self.curRelation = 'DerivedFrom'
            else:
                self.curRelation = None
                if pos in PARTS_OF_SPEECH:
                    self.pos = PARTS_OF_SPEECH[pos]
        elif language_match:
            self.lang = language_match.group(1)
            self.langcode = LANGUAGES.get(self.lang)
        elif chinese_match:
            scripttag = chinese_match.group(2)
            self.locales = []
            if 's' in scripttag:
                self.locales.append('_CN')
            if 't' in scripttag:
                self.locales.append('_TW')
        elif line[0:1] == '#' and self.lang != 'English' and self.lang is not None:
            defn = line[1:].strip()
            if defn[0:1] not in ':*#':
                for defn2 in filter_line(defn):
                    if not ascii_enough(defn2): continue
                    if 'Index:' in title: continue
                    if self.langcode == 'zh':
                        for locale in self.locales:
                            self.output_translation(title, defn2, locale)
                    elif self.langcode:
                        self.output_translation(title, defn2)
        elif line[0:4] == '----':
            self.pos = None
            self.lang = None
            self.langcode = None
            self.curRelation = None
        elif trans_top_match:
            pos = self.pos or 'n'
            sense = trans_top_match.group(1).split(';')[0].strip('.')
            if 'translations' in sense.lower():
                self.curSense = None
            else:
                self.curSense = (pos, sense)
        elif trans_tag_match:
            lang = trans_tag_match.group(1)
            translation = trans_tag_match.group(2)
            if self.curSense is not None and self.lang == 'English':
                # handle Chinese separately
                if lang not in ('cmn', 'yue', 'zh-yue', 'zh'):
                    self.output_sense_translation(lang, translation, title,
                                                  self.curSense)
        elif '{{trans-bottom}}' in line:
            self.curSense = None
        elif line.startswith('* ') and self.curRelation and self.langcode:
            relatedmatch = WIKILINK.search(line)
            if relatedmatch:
                related = relatedmatch.group(1)
                self.output_monolingual(self.langcode, self.curRelation,
                                        related, title)

    def output_monolingual(self, lang, relation, term1, term2):
        if term_is_bad(term1) or term_is_bad(term2):
            return
        source = normalized_concept_uri(lang, term1)
        if self.pos:
            target = normalized_concept_uri(lang, term2, self.pos)
        else:
            target = normalized_concept_uri(lang, term2)
        surfaceText = "[[%s]] %s [[%s]]" % (term1, relation, term2)

        edge = make_edge('/r/'+relation, source, target, '/d/wiktionary/%s/%s' % (lang, lang),
                         license=Licenses.cc_sharealike,
                         sources=[SOURCE, MONOLINGUAL],
                         weight=1.0,
                         surfaceText=surfaceText)
        self.writer.write(edge)

    def output_sense_translation(self, lang, foreign, english, sense):
        pos, disambiguation = sense
        if 'Wik' in foreign or 'Wik' in english or term_is_bad(foreign) or term_is_bad(english):
            return
        # Quick fix that drops definitions written in Lojban syntax
        if lang == 'jbo' and re.search(r'x[1-5]', english):
            return
        if lang == 'zh-cn':
            lang = 'zh_CN'
        elif lang == 'zh-tw':
            lang = 'zh_TW'
        source = normalized_concept_uri(
          lang, unicodedata.normalize('NFKC', foreign)
        )
        target = normalized_concept_uri(
          'en', english, pos, disambiguation
        )
        relation = '/r/TranslationOf'
        try:
            surfaceRel = "is %s for" % (CODE_TO_ENGLISH_NAME[lang.split('_')[0]])
        except KeyError:
            surfaceRel = "is [language %s] for" % lang
        surfaceText = "[[%s]] %s [[%s (%s)]]" % (foreign, surfaceRel, english, disambiguation.split('/')[-1].replace('_', ' '))
        edge = make_edge(relation, source, target, '/d/wiktionary/en/%s' % lang,
                         license=Licenses.cc_sharealike,
                         sources=[SOURCE, TRANSLATE],
                         weight=1.0,
                         surfaceText=surfaceText)
        self.writer.write(edge)

    def output_translation(self, foreign, english, locale=''):
        if term_is_bad(foreign) or term_is_bad(english):
            return
        # Quick fix that drops definitions written in Lojban syntax
        if self.langcode == 'jbo' and re.search(r'x[1-5]', english):
            return
        source = normalized_concept_uri(
            self.langcode + locale,
            foreign
        )
        target = normalized_concept_uri(
          'en', english
        )
        relation = '/r/TranslationOf'
        try:
            surfaceRel = "is %s for" % (CODE_TO_ENGLISH_NAME[self.langcode.split('_')[0]])
        except KeyError:
            surfaceRel = "is [language %s] for" % self.langcode
        surfaceText = "[[%s]] %s [[%s]]" % (foreign, surfaceRel, english)
        edge = make_edge(relation, source, target, '/d/wiktionary/en/%s' % self.langcode,
                         license=Licenses.cc_sharealike,
                         sources=[SOURCE, INTERLINGUAL],
                         weight=1.0,
                         surfaceText=surfaceText)
        self.writer.write(edge)

def filter_line(line):
    line = re.sub(r"\{\{.*?\}\}", "", line)
    line = re.sub(r"<.*?>", "", line)
    line = re.sub(r"\[\[([^|]*\|)?(.*?)\]\]", r"\2", line)
    line = re.sub(r"''+", "", line)
    line = re.sub(r"\(.*?\(.*?\).*?\)", "", line)
    line = re.sub(r"\(.*?\)", "", line)
    if re.search(r"\.\s+[A-Z]", line): return
    parts = re.split(r"[,;:/]", line)
    for part in parts:
        if not re.search(r"(singular|plural|participle|preterite|present|-$)", part):
            remain = part.strip().strip('.').strip()
            if remain: yield remain


def handle_file(input_file, output_file):
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = FindTranslations(output_file=output_file)

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    if hasattr(input_file, 'read'):
        input_stream = input_file
    else:
        input_stream = open(input_file)
    parser.parse(input_stream)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='XML file of input')
    parser.add_argument('output', help='JSON-stream file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)

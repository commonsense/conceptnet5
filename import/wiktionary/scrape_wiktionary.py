#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
from metanl import english
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.iso639 import langs
import unicodedata
import string
import re
import sys

def ascii_enough(text):
    # cheap assumption: if it's ASCII, and it's meant to be in English, it's
    # probably actually in English.
    return text.encode('ascii', 'replace') == text

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
    u'英語': 'en',
    u'日本語': 'ja'
}

SOURCE = '/s/web/en.wiktionary.org'
INTERLINGUAL = '/s/rule/wiktionary_interlingual_definitions'
MONOLINGUAL = '/s/rule/wiktioary_monolingual_definitions'
TRANSLATE = '/s/rule/wiktionary_translation_tables'
DEFINE = '/s/rule/wiktionary_define_senses'

class FindTranslations(ContentHandler):
    def __init__(self):
        self.lang = None
        self.langcode = None
        self.inArticle = False
        self.inTitle = False
        self.curSense = None
        self.curTitle = ''
        self.curText = ''
        self.locales = []
        self.curRelation = None
        self.writer = MultiWriter('wiktionary')

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
                self.curRelation = 'ConceptuallyRelatedTo'
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
                self.curSense = pos+'/'+sense
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
        if 'Wik' in term1 or 'Wik' in term2:
            return
        source = make_concept_uri(term1, lang)
        if self.pos:
            target = make_concept_uri(term2, lang, self.pos)
        else:
            target = make_concept_uri(term2, lang)
        surfaceText = "[[%s]] %s [[%s]]" % (term1, relation, term2)
        print surfaceText

        edge = make_edge('/r/'+relation, source, target, '/d/wiktionary/%s/%s' % (lang, lang),
                         license='/l/CC/By-SA',
                         sources=[SOURCE, MONOLINGUAL],
                         context='/ctx/all',
                         weight=1.5,
                         surfaceText=surfaceText)
        self.writer.write(edge)

    def output_sense_translation(self, lang, foreign, english, disambiguation):
        if 'Wik' in foreign or 'Wik' in english:
            return
        if lang == 'zh-cn':
            lang = 'zh_CN'
        elif lang == 'zh-tw':
            lang = 'zh_TW'
        source = make_concept_uri(
          unicodedata.normalize('NFKC', foreign), lang
        )
        target = make_concept_uri(
          english, 'en', disambiguation
        )
        relation = '/r/TranslationOf'
        try:
            surfaceRel = "is %s for" % (langs.english_name(lang))
        except KeyError:
            surfaceRel = "is [language %s] for" % lang
        surfaceText = "[[%s]] %s [[%s (%s)]]" % (foreign, surfaceRel, english, disambiguation.split('/')[-1].replace('_', ' '))
        print surfaceText
        edge = make_edge(relation, source, target, '/d/wiktionary/en/%s' % lang,
                         license='/l/CC/By-SA',
                         sources=[SOURCE, TRANSLATE],
                         context='/ctx/all',
                         weight=1.5,
                         surfaceText=surfaceText)
        self.writer.write(edge)
        
    def output_translation(self, foreign, english, locale=''):
        source = make_concept_uri(
          unicodedata.normalize('NFKC', foreign),
          self.langcode+locale
        )
        target = make_concept_uri(
          english, 'en'
        )
        relation = '/r/TranslationOf'
        try:
            surfaceRel = "is %s for" % (langs.english_name(self.langcode))
        except KeyError:
            surfaceRel = "is [language %s] for" % self.langcode
        surfaceText = "[[%s]] %s [[%s]]" % (foreign, surfaceRel, english)
        edge = make_edge(relation, source, target, '/d/wiktionary/en/%s' % self.langcode,
                         license='/l/CC/By-SA',
                         sources=[SOURCE, INTERLINGUAL],
                         context='/ctx/all',
                         weight=1.5,
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

if __name__ == '__main__':
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = FindTranslations()

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    parser.parse(open("enwiktionary.xml"))


#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
from metanl import english
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.iso639 import langs
from languages_3_to_2 import LANGUAGES_3_TO_2
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
TRANS_BOTTOM = re.compile(r"\{\{trans-bottom\|(.+)\}\}")
TRANS = re.compile(r"====\{\{trans\}\}====")
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
MONOLINGUAL = '/s/rule/wiktionary_monolingual_definitions'
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
        self.nosensetrans = None # non-sense-specific translation

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
        trans_bottom_match = TRANS_BOTTOM.match(line)
        trans_match = TRANS.match(line)
        trans_tag_match = TRANS_TAG.search(line)
        chinese_match = CHINESE_TAG.search(line)
        
        ### Get sense-specific translation
        if trans_top_match: # start translation part
            pos = self.pos or 'n'
            # get translation sense
            sense = trans_top_match.group(1).split(';')[0].strip('.')
            self.curSense = pos+'/'+sense
            return
        if trans_bottom_match: # end translation part
            self.curSense = None
            return
        if self.curSense and line[0:5] == '*[[{{': # get translation
            lang = line[5:8] # get language of translation
            if lang in LANGUAGES_3_TO_2: # convert 3-letter code to 2-letter code
                lang = LANGUAGES_3_TO_2[lang]
            elif lang not in LANGUAGES_3_TO_2.values(): # if 3-letter code not found, guess english
                lang = 'en'
            # find all translations of that language
            translations = re.findall(r"\[\[(.*?)\]\]", line)[1:] 
            for translation in translations: # iterate over translations
                open_paren_pos = translation.find('(') # look for open paren -- maybe part of speech
                if open_paren_pos != -1: # contains open paren
                    translation = translation[:open_paren_pos] # delete after paren
                self.output_sense_translation(lang, translation, title, \
                                              self.curSense)
            return

        ### Get relation
        if line.startswith('===={{rel}}===='): # start relation part
            self.curRelation = 'ConceptuallyRelatedTo'
            return
        if self.curRelation: # within relation part
            if line.startswith('*'): # get relation
                relations = re.findall(r"\{\{(.*?)\}\}", line)
                if len(relations) > 0:
                    if relations[0] == 'syn': # synonym
                        self.curRelation = 'Synonym'
                    if relations[0] == 'drv': # derivative
                        self.curRelation = 'Derivative'                    
                related_words = re.findall(r"\[\[(.*?)\]\]", line)
                for related_word in related_words:
                    self.output_monolingual('jpn', self.curRelation, \
                                            related_word, title)
                self.curRelation = 'ConceptuallyRelatedTo' # back to default
            else:
                self.curRelation = None

        ### Get non-sense-specific translation
        if trans_match: 
            self.nosensetrans = 1 # *maybe* start non-sense-specific translation
        if self.nosensetrans == 1 and line.startswith('{{top}}'):
            self.nosensetrans = 2 # start non-sense-specific translation            
        if self.nosensetrans == 2:
            if line.startswith('{{bottom}}'):
                self.nosensetrans = None
                return
            if line.startswith('*{{'):
                lang = line[3:6]
                if lang in LANGUAGES_3_TO_2: # convert 3-letter code to 2-letter code
                    lang = LANGUAGES_3_TO_2[lang]
                elif lang not in LANGUAGES_3_TO_2.values(): # if 3-letter code not found, guess english
                    lang = 'en'
                translations = re.findall(r"\[\[(.*?)\]\]", line)
                for translation in translations:
                    open_paren_pos = translation.find('(') # look for open paren -- maybe part of speech
                    if open_paren_pos != -1: # contains open paren
                        translation = translation[:open_paren_pos] # delete after paren
                    self.output_sense_translation(lang, translation, title, '')
    
    def output_monolingual(self, lang, relation, term1, term2):
        if 'Wik' in term1 or 'Wik' in term2:
            return
        source = make_concept_uri(term1, lang)
        if self.pos:
            target = make_concept_uri(term2, lang, self.pos)
        else:
            target = make_concept_uri(term2, lang)
        surfaceText = "[[%s]] %s [[%s]]" % (term1, relation, term2)
        #print surfaceText

        edge = make_edge('/r/'+relation, source, target, '/d/wiktionary/%s/%s' % (lang, lang),
                         license='/l/CC/By-SA',
                         sources=[SOURCE, MONOLINGUAL],
                         context='/ctx/all',
                         weight=1.5,
                         surfaceText=surfaceText)
        self.writer.write(edge)

    def output_sense_translation(self, lang, foreign, japanese, disambiguation):
        if 'Wik' in foreign or 'Wik' in japanese:
            return
        if lang == 'zh-cn':
            lang = 'zh_CN'
        elif lang == 'zh-tw':
            lang = 'zh_TW'
        source = make_concept_uri(
          unicodedata.normalize('NFKC', foreign), lang
        )
        target = make_concept_uri(
          japanese, 'ja', disambiguation
        )
        relation = '/r/TranslationOf'
        try:
            surfaceRel = "is %s for" % (langs.english_name(lang))
        except KeyError:
            surfaceRel = "is [language %s] for" % lang
        surfaceText = "[[%s]] %s [[%s (%s)]]" % (foreign, surfaceRel, english, disambiguation.split('/')[-1].replace('_', ' '))
        #print surfaceText
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
    parser.parse(open("raw_data/jawiktionary.xml"))


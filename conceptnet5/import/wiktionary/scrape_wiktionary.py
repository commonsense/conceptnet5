#!/usr/bin/env python
from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize
import unicodedata
import re
import sys

def english_normalize(text):
    if text.startswith('to '):
        text = text[3:]
    result = normalize(unicodedata.normalize('NFKC', text))
    return result

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
}

class FindTranslations(ContentHandler):
    def __init__(self):
        self.lang = None
        self.langcode = None
        self.inArticle = False
        self.inTitle = False
        self.curSense = None
        self.curTitle = ''
        self.curText = ''
        self.locales = None
        self.curRelation = None

        self.graph = JSONWriterGraph('../json_data/wiktionary_all')

        source = self.graph.get_or_create_node('/source/web/en.wiktionary.org')
        rule = self.graph.get_or_create_node('/source/rule/wiktionary_interlingual_definitions')
        monolingual_rule = self.graph.get_or_create_node('/source/rule/wiktionary_monolingual_definitions')
        wordsense_rule = self.graph.get_or_create_node('/source/rule/wiktionary_translation_tables')
        sense_define_rule = self.graph.get_or_create_node('/source/rule/wiktionary_define_senses')
        self.graph.justify('/', source)
        self.graph.justify('/', rule)
        self.graph.justify('/', monolingual_rule)
        self.graph.justify('/', wordsense_rule)
        self.graph.justify('/', sense_define_rule)

        self.conjunction = self.graph.get_or_create_conjunction([source, rule])
        self.monolingual_conjunction = self.graph.get_or_create_conjunction([source, monolingual_rule])
        self.wordsense_conjunction = self.graph.get_or_create_conjunction([source, wordsense_rule])
        self.defn_conjunction = self.graph.get_or_create_conjunction([source, sense_define_rule])

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
            if len(self.curText) > 100:
                # bail out
                self.inArticle = False

    def handleArticle(self, title, text):
        lines = text.split('\n')
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
                self.curRelation = 'DerivedFrom'
            else:
                self.curRelation = None
                if pos in PARTS_OF_SPEECH:
                    self.pos = PARTS_OF_SPEECH[pos]
                else:
                    self.pos = None
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
            sense = trans_top_match.group(1)
            self.curSense = pos+'/'+sense
            if self.lang == 'English':
                self.output_sense(title, self.curSense)
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
        source = self.graph.get_or_create_concept(lang, term1)
        target = self.graph.get_or_create_concept(lang, term2)
        relation = self.graph.get_or_create_relation(relation)
        assertion = self.graph.get_or_create_assertion(
          relation, [source, target],
          {'dataset': 'wiktionary/en/%s' % lang,
           'license': 'CC-By-SA', 'normalized': False}
        )
        self.graph.justify(self.monolingual_conjunction, assertion)
        print assertion.encode('utf-8')


    def output_sense_translation(self, lang, foreign, english, disambiguation):
        if lang == 'zh-cn':
            lang = 'zh_CN'
        elif lang == 'zh-tw':
            lang = 'zh_TW'
        source = self.graph.get_or_create_concept(
          lang,
          unicodedata.normalize('NFKC', foreign)
        )
        target = self.graph.get_or_create_concept(
          'en', english, disambiguation
        )
        relation = self.graph.get_or_create_relation(
          'TranslationOf'
        )
        assertion = self.graph.get_or_create_assertion(
          relation, [source, target],
          {'dataset': 'wiktionary/en/%s' % lang,
           'license': 'CC-By-SA', 'normalized': False}
        )
        self.graph.justify(self.conjunction, assertion)
        print assertion.encode('utf-8')
        
    def output_sense(self, english, disambiguation):
        source = self.graph.get_or_create_concept(
          'en', english, disambiguation
        )
        definition = self.graph.get_or_create_concept(
          'en', disambiguation[2:]
        )
        definition_norm = self.graph.get_or_create_concept(
          'en', english_normalize(disambiguation[2:])
        )
        relation = self.graph.get_or_create_relation(
          'DefinedAs'
        )
        assertion = self.graph.get_or_create_assertion(
          relation, [source, definition],
          {'dataset': 'wiktionary/en/en',
           'license': 'CC-By-SA', 'normalized': False}
        )
        norm_assertion = self.graph.get_or_create_assertion(
          relation, [source, definition_norm],
          {'dataset': 'wiktionary/en/en',
           'license': 'CC-By-SA', 'normalized': True}
        )

        self.graph.justify(self.defn_conjunction, assertion)
        self.graph.derive_normalized(assertion, norm_assertion)
        print assertion.encode('utf-8')

    def output_translation(self, foreign, english, locale=''):
        source = self.graph.get_or_create_concept(
          self.langcode+locale,
          unicodedata.normalize('NFKC', foreign)
        )
        target = self.graph.get_or_create_concept(
          'en', english
        )
        relation = self.graph.get_or_create_relation(
          'TranslationOf'
        )
        assertion = self.graph.get_or_create_assertion(
          relation, [source, target],
          {'dataset': 'wiktionary/en/%s' % self.langcode,
           'license': 'CC-By-SA', 'normalized': False}
        )
        target_normal = self.graph.get_or_create_concept(
          'en', english_normalize(english)
        )
        assertion_normal = self.graph.get_or_create_assertion(
          relation, [source, target_normal],
          {'dataset': 'wiktionary/%s' % self.langcode,
           'license': 'CC-By-SA', 'normalized': True}
        )
        self.graph.justify(self.conjunction, assertion)
        self.graph.derive_normalized(assertion, assertion_normal)
        
        print assertion.encode('utf-8')

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


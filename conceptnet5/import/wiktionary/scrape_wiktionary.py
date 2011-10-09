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
    print result
    return result

def ascii_enough(text):
    # cheap assumption: if it's ASCII, and it's meant to be in English, it's
    # probably actually in English.
    return text.encode('ascii', 'replace') == text

class FindTranslations(ContentHandler):
    def __init__(self, lang='Portuguese', code='pt'):
        self.lang = lang
        self.langcode = code
        self.regex = re.compile(r'==\s*(' + lang + r')\s*==')
        self.inArticle = False
        self.inTitle = False
        self.curTitle = ''
        self.curText = ''

        self.graph = JSONWriterGraph('../json_data/wiktionary_%s' % code)

        source = self.graph.get_or_create_node('/source/web/en.wiktionary.org')
        rule = self.graph.get_or_create_node('/source/rule/scan_wiktionary_definitions')
        self.graph.justify('/', source)
        self.graph.justify('/', rule)

        self.conjunction = self.graph.get_or_create_conjunction([source, rule])

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
        lang = False
        match = self.regex.search(text)
        if match:
            lines = text[match.end():].split('\n')
            for line in lines:
                if line[0:1] == '#':
                    defn = line[1:].strip()
                    if defn[0:1] not in ':*#':
                        for defn2 in filter_line(defn):
                            if not ascii_enough(defn2): continue
                            source = self.graph.get_or_create_concept(
                              self.langcode,
                              unicodedata.normalize('NFKC', title)
                            )
                            target = self.graph.get_or_create_concept(
                              'en', defn2
                            )
                            relation = self.graph.get_or_create_relation(
                              'TranslationOf'
                            )
                            assertion = self.graph.get_or_create_assertion(
                              relation, [source, target],
                              {'dataset': 'wiktionary/definitions/%s' % self.langcode,
                               'license': 'CC-By-SA', 'normalized': False}
                            )
                            target_normal = self.graph.get_or_create_concept(
                              'en', normalize(defn2)
                            )
                            assertion_normal = self.graph.get_or_create_assertion(
                              relation, [source, target_normal],
                              {'dataset': 'wiktionary/definitions/%s' % self.langcode,
                               'license': 'CC-By-SA', 'normalized': True}
                            )
                            self.graph.justify(self.conjunction, assertion)
                            self.graph.derive_normalized(assertion, assertion_normal)
                            
                            print assertion
                elif line[0:4] == '----':
                    return

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
    import sys
    if len(sys.argv) <= 1:
        print "usage: scrape_wiktionary.py [English name of language] [language code]"
        print "example: scrape_wiktionary.py Portuguese pt"
        sys.exit(1)
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = FindTranslations(sys.argv[1], sys.argv[2])

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    parser.parse(open("enwiktionary.xml"))


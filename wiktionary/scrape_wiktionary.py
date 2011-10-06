#!/usr/bin/env python
from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
from unicodedata import normalize
import re
import sys

class FindTranslations(ContentHandler):
    def __init__(self, lang='Portuguese'):  
        self.lang = lang
        self.regex = re.compile(r'==\s*(' + lang + r')\s*==')
        self.inArticle = False
        self.inTitle = False
        self.curTitle = ''
        self.curText = ''

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
                            print normalize('NFKC', '%s = %s' % (title,
                            defn2)).encode('utf-8')
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
        print "usage: scrape_wiktionary.py [English name of language]"
        print "example: scrape_wiktionary.py Portuguese"
        sys.exit(1)
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = FindTranslations(sys.argv[1])

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    parser.parse(open("enwiktionary.xml"))


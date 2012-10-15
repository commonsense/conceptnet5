import codecs
import re
from ftfy import ftfy

def get_lang(concept):
    return concept.split(u'/')[2]

def fix(text):
    return ftfy(text).lower()

used = set()
with codecs.open('data/flat/COREPLUS', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if line:
            parts = line.split(u'\t')
            source, target = parts[2], parts[3]
            if source.startswith(u'/c/') and target.startswith(u'/c/'):
                sourcelang = get_lang(source)
                targetlang = get_lang(target)
                text = parts[-1]
                if text:
                    matches = re.findall(ur'\[\[(.+?)\]\]', text)
                    if len(matches) == 2:
                        source_concept = (sourcelang, fix(matches[0].strip(u'[]')))
                        target_concept = (targetlang, fix(matches[1].strip(u'[]')))
                        for concept in (source_concept, target_concept):
                            if u' ' not in concept[1]:
                                if concept not in used:
                                    used.add(concept)
                                    print (u'%s\t%s' % concept).encode('utf-8')

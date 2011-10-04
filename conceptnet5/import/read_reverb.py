"""
Parse the ReVerb dataset and put assertions to ConceptNet 5
"""
from conceptnet5.graph import get_graph
from simplenlp import get_nl
from urlparse import urlparse
import codecs
import nltk
import os

GRAPH = get_graph()
nl = get_nl('en')

reverb = GRAPH.get_or_create_node(u'/source/rule/reverb')
GRAPH.justify(0, reverb)
reverb_object = GRAPH.get_or_create_node(u'/source/rule/extract_reverb_objects')
GRAPH.justify(0, reverb_object)

def contain_single_be(tokens, tags):
    be = ['is', 'are', 'was', 'were', 'be']
    verbs = filter(lambda x: x.startswith('V'), tags)
    if len(verbs) == 1 and tokens[tags.index(verbs[0])] in be:
        return tags.index(verbs[0])
    elif len(verbs) == 2 and tokens[tags.index(verbs[1])] == 'been':
        return tags.index(verbs[1])
    return -1

def index_of_tag(tags, target):
    if target in tags:
        return tags.index(target)
    return -1

def index_of_be(tokens):
    be = ['is', 'are', 'was', 'were', 'be', 'been']
    for token in tokens:
        if token in be:
            return tokens.index(token)
    return -1

def index_of_verbs(tags):
    index = []
    for tag in tags:
        if tag.startswith('V'):
            index.append(tags.index(tag))
    return index

def remove_tags(tokens, tags, target):
    index_rb = 0
    if target in tags:
        index_rb = tags.index(target)
    if index_rb > 0:
      tokens.remove(tokens[index_rb])
      tags.remove(tags[index_rb])
    return tokens, tags

def get_domain_names(urls):
    parsed_urls = map(lambda x: urlparse(x), urls)
    domain_names = map(lambda x: x.netloc, parsed_urls)
    return domain_names

def output_sentence(arg1, arg2, arg3, relation, \
    raw_arg1, raw_arg2, raw_relation, urls, prep=None):
    if arg2.strip() == "": # Remove "A is for B" sentence
        return
    arg1 = nl.normalize(arg1).strip()
    arg2 = nl.normalize(arg2).strip()
    assertion = None
    if arg3 == None:
        print '%s(%s, %s)' % (relation, arg1, arg2)
        assertion = GRAPH.get_or_create_assertion(
            '/relation/'+relation,
            ['/concept/en/'+arg1, '/concept/en/'+arg2],
            {'dataset': 'reverb/en'}
        )
    else:
        if arg3.strip() == "": # Remove "A before/after/off" sentence
            return
        arg3 = nl.normalize(arg3).strip()
        print '%s(%s, %s), %s(%s, %s)' % \
            (relation, arg1, arg2, prep, arg2, arg3)
        assertion1 = GRAPH.get_or_create_assertion(
            '/relation/'+relation,
            ['/concept/en/'+arg1, '/concept/en/'+arg2],
            {'dataset': 'reverb/en'}
        )
        assertion2 = GRAPH.get_or_create_assertion(
            '/concept/en'+prep,
            ['/concept/en/'+arg2, '/concept/en/'+arg3],
            {'dataset': 'reverb/en'}
        )
        assertion = GRAPH.get_or_create_conjunction([assertion1, assertion2])
    frame = u"{1}%s{2}" % (raw_relation)
    raw = GRAPH.get_or_create_assertion(
        '/frame/en/'+frame,
        [u'/concept/en/'+raw_arg1, u'/concept/en/'+raw_arg2],
        {'dataset': 'reverb/en'}
    )
    for domain in set(get_domain_names(urls.split('|'))):
        source_uri = u"/source/source/web/%s" % domain
        source = GRAPH.get_or_create_node(source_uri)
        GRAPH.justify(0, source, weight=0.5)
        conjunction = \
            GRAPH.get_or_create_conjunction([source, reverb, reverb_object])
        """
        The assertions start with numbers are really bad in ReVerb.
        We set a small weight on the justification edge.
        """
        if raw_arg1[0].isdigit():
            GRAPH.justify(conjunction, raw, weight=0.2)
        else:
            GRAPH.justify(conjunction, raw, weight=0.7)
        print GRAPH.derive_normalized(raw, assertion)

def handle_file(filename):
    for line in codecs.open(filename, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            parts = line.split('\t')
            if len(parts) < 10:
                continue
            id, old_arg1, old_rel, old_arg2, nor_arg1, nor_rel, nor_arg2, \
                num_sentence, confidence, url = parts
            sentence = "%s %s %s" % (old_arg1, old_rel, old_arg2)
            tokens = nltk.word_tokenize(sentence)
            tags = map(lambda x: x[1], nltk.pos_tag(tokens))
            tokens, tags = remove_tags(tokens, tags, 'RB')	# Remove adverb
            tokens, tags = remove_tags(tokens, tags, 'MD')	# Remove modals
            tokens = map(lambda x: x.lower(), tokens)

            index_verbs = index_of_verbs(tags)
            if len(index_verbs) == 0: continue
            index_be = contain_single_be(tokens, tags)
            if index_be == len(tokens) - 1: continue
            index_prep = 0
            if 'IN' in tags:
                if tags.index('IN') > index_verbs[0]:
                    index_prep = tags.index('IN')
            if 'TO' in tags:
                index_to = tags.index('TO')
                if ((index_to < index_prep and index_prep > 0) or \
                    (index_prep == 0)) and (index_to > index_verbs[0]):
                    index_prep = tags.index('TO')
            if index_be > 0:
                if tokens[index_be] == 'been':
                    arg1 = " ".join(tokens[:index_be-1])
                else:
                    arg1 = " ".join(tokens[:index_be])
                next_tag = tags[index_be+1]
                if next_tag == 'DT': # IsA relation
                    if index_prep == 0:
                        arg2 = " ".join(tokens[index_be+2:])
                        output_sentence(arg1, arg2, None, 'IsA', \
                            old_arg1, old_arg2, old_rel, url)
                    else:
                        if tokens[index_prep] == 'of' and \
                            tokens[index_prep-1] == 'kind': # 'a kind of' frame
                            arg2 = " ".join(tokens[index_prep+1:])
                            output_sentence(arg1, arg2, None, 'IsA', \
                                old_arg1, old_arg2, old_rel, url)
                        else:
                            arg2 = " ".join(tokens[index_be+2:index_prep])
                            arg3 = " ".join(tokens[index_prep+1:])
                            output_sentence(arg1, arg2, arg3, 'IsA', \
                                old_arg1, old_arg2, old_rel, url, \
                                tokens[index_prep])
                else: # HasProperty relation
                    if index_prep == 0:
                        arg2 = " ".join(tokens[index_be+1:])
                        output_sentence(arg1, arg2, None, 'HasProperty', \
                            old_arg1, old_arg2, old_rel, url)
                    else:
                        arg2 = " ".join(tokens[index_be+1:index_prep])
                        arg3 = " ".join(tokens[index_prep+1:])
                        output_sentence(arg1, arg2, arg3, \
                            'HasProperty', old_arg1, old_arg2, old_rel, url, \
                            tokens[index_prep])
            else:
                index_be = index_of_be(tokens)
                if index_be == len(tokens) - 1: continue
                if (index_be > 0) and \
                    (index_verbs[0] == index_be or \
                    len(index_verbs) > 1): 
                    if tokens[index_be] == 'been':
                        arg1 = " ".join(tokens[:index_be-1])
                    else:
                        arg1 = " ".join(tokens[:index_be])
                    if tags[index_be+1] == 'VBG': 
                        relation = 'SubjectOf'
                    else: 
                        relation = 'DirectObjectOf'
                    if index_prep == 0:
                        arg2 = " ".join(tokens[index_be+1:])
                        output_sentence(arg1, arg2, None, relation, \
                            old_arg1, old_arg2, old_rel, url)
                    else:
                        arg2 = " ".join(tokens[index_be+1:index_prep])
                        arg3 = " ".join(tokens[index_prep+1:])
                        output_sentence(arg1, arg2, arg3, relation, \
                            old_arg1, old_arg2, old_rel, url, \
                            tokens[index_prep])
                else: # SubjectOf relation
                    if index_prep > 0:
                        arg1 = " ".join(tokens[:index_verbs[0]])
                        arg2 = " ".join(tokens[index_verbs[0]:index_prep])
                        arg3 = " ".join(tokens[index_prep+1:])
                        output_sentence(arg1, arg2, arg3, 'SubjectOf', \
                            old_arg1, old_arg2, old_rel, url, \
                            tokens[index_prep])


if __name__ == '__main__':
    for filename in os.listdir('.'):
        if filename.startswith('reverb'):
            handle_file(filename)

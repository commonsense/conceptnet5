from __future__ import unicode_literals, print_function
import xmltodict
import re
import codecs
import langcodes
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri, valid_concept_name
from conceptnet5.edges import make_edge


# Now that Unicode literals are on, get the type of a Unicode string,
# regardless of whether this is Python 2 or 3.
STRING_TYPE = type("")

# I took the time to record these, but in the end I don't think I plan
# to use them. Japanese parts of speech don't fit neatly enough into
# ConceptNet's neat n/v/a/r types.
#
# The idea was to record the parts of speech by the first 10 characters
# of their category in JMdict (because they're automatically decoded
# from their more helpful entity form).
NOUN_TYPES = [
    "noun (comm",
    "adverbial ",
    "noun, used",
    "noun (temp",
    "noun or pa",
]
ADJ_TYPES = [
    "nouns whic",  # I promise this is more like an adjective than a noun. Its entity is &adj-no;
    "adjective ",
    "adjectival",
    "pre-noun a",
]
ADV_TYPES = [
    "adverb (fu",
    "adverb tak",
]
VERB_TYPES = [
    "Ichidan ve",
    "Nidan verb",
    "Yodan verb",
    "Godan verb",
    "intransiti",
    "Kuru verb ",
    "irregular ",
    "su verb - ",
    "suru verb ",
]


def convert_lang_code(code):
    """
    Map a language code to the canonical one that ConceptNet 5 uses, using the
    'langcodes' library.
    """
    return str(langcodes.get(code))


def fix_context(context):
    ending = ' term'
    if context.endswith(ending):
        return context[:-len(ending)]
    return context


def get_list(node, tag):
    """
    Get sub-nodes of this node by their tag, and make sure to return a list.

    The problem here is that xmltodict returns a nested dictionary structure,
    whose substructures have different *types* if there's repeated nodes
    with the same tag. So a list of one thing ends up being a totally different
    thing than a list of two things.

    So, here, we look up a sub-node by its tag, and return a list regardless of
    whether it matched 0, 1, or more things.
    """
    subnode = node.get(tag, [])
    if isinstance(subnode, list):
        return subnode
    else:
        return [subnode]


GLOSS_RE = re.compile(r'''
    # Separate out text in parentheses or brackets.
    ^
    (\(.*?\)|\[.*?\] )?   # possibly a bracketed expression before the gloss
    (.*?)                 # the gloss itself
    ( \(.*?\)|\[.*?\])?   # possibly a bracketed expression after the gloss
    $
''', re.VERBOSE)


def parse_gloss(text):
    matched = GLOSS_RE.match(text)
    if matched:
        return matched.group(2).strip()
    else:
        return None


def handle_file(filename, output_file):
    """
    JMdict is a Japanese translation dictionary, targeting multiple languages,
    released under a Creative Commons Attribution-ShareAlike license. That's
    awesome.

    It's released as a kind of annoying XML structure, using fancy XML features
    like entities, so in order to read it we need a full-blown XML parser. Python's
    built-in XML parsers are horrifying, so here we use the 'xmltodict' module, which
    is also horrifying but gets the job done.

    The majorly weird thing about xmltodict that we have to work around is that
    it gives results of different *types* when you get 0, 1, or many child nodes.
    This is what get_list is for.
    """
    # Read the XML file as UTF-8, and parse it into a dictionary.
    file = codecs.open(filename, encoding='utf-8')
    out = MsgpackStreamWriter(output_file)
    data = file.read()
    file.close()
    xml = xmltodict.parse(data)

    # The dictionary contains a list of <entry> tags.
    root_node = xml['JMdict']
    for entry in get_list(root_node, 'entry'):
        # From JMdict's documentation: "The kanji element, or in its absence,
        # the reading element, is the defining component of each entry."
        #
        # Quick summary of what's going on here: most Japanese words can be
        # written using kanji or kana.
        #
        # Kana are phonetic characters. Every word can be written in kana, in
        # one of two alphabets (hiragana or katakana). Words that are homonyms
        # have the same kana, unless they're written in different alphabets.
        #
        # Kanji are Chinese-based characters that are related to the meaning of
        # the word. They're compact and good at disambiguating homonyms, so
        # kanji are usually used as the canonical representation of a word.
        # However, some words have no kanji.
        #
        # The kana version of a word written in kanji is called its 'reading'.
        # Words that are pronounced differently in different contexts have
        # multiple readings.
        #
        # Okay, done with the intro to Japanese orthography. In JMdict, if
        # a word can be written in kanji, it has a <k_ele> element, containing
        # a <keb> element that contains the text. Every word also has an
        # <r_ele> element, containing one or more <reb> elements that are phonetic
        # readings of the word.
        #
        # We get the "defining text" of a word by taking its <keb> if it exists,
        # or all of its <reb>s if not. There's no way to tell which <reb> is the
        # most "defining" in the case where there's no <keb>.
        headwords = [word['keb'] for word in get_list(entry, 'k_ele')]
        if not headwords:
            headwords = [word['reb'] for word in get_list(entry, 'r_ele')]

        # An entry might have different word senses that are translated
        # differently to other languages. Ideally, we'd remember that they're
        # different senses. However, we have no way to refer to the different
        # senses. So for now, we disregard word senses. One day we might have
        # a better overall plan for word senses in ConceptNet.
        senses = get_list(entry, 'sense')
        for sense_num, sense in enumerate(senses):
            # Glosses are translations of the word to different languages.
            # If the word is a loan-word, the foreign word it was derived from
            # will be marked with the <lsource> tag instead of <gloss>.
            #
            # Get all the glosses, including the lsource if it's there.
            glosses = get_list(sense, 'gloss') + get_list(sense, 'lsource')
            contexts = [
                fix_context(context)
                for context in get_list(sense, 'field')
            ]
            pos = '_'
            for pos_tag in get_list(sense, 'pos'):
                if pos_tag[:10] in NOUN_TYPES:
                    pos = 'n'
                elif pos_tag[:10] in VERB_TYPES:
                    pos = 'v'
                elif pos_tag[:10] in ADJ_TYPES:
                    pos = 'a'
                elif pos_tag[:10] in ADV_TYPES:
                    pos = 'r'

            for gloss in glosses:
                if '#text' in gloss:
                    # A gloss node might be marked with a 'lang' attribute. If so,
                    # xmltodict represents it as a dictionary with '#text' and
                    # '@xml:lang' elements.
                    text = parse_gloss(gloss['#text'])
                    lang = convert_lang_code(gloss['@xml:lang'])
                elif isinstance(gloss, STRING_TYPE):
                    # If there's no 'lang' attribute, the gloss is in English,
                    # and xmltodict gives it to us as a plain Unicode string.
                    lang = 'en'
                    text = parse_gloss(gloss)

                # If we parsed the node at all and the text looks good, then we can
                # add edges to ConceptNet.
                #
                # We don't want to deal with texts with periods (these might be
                # dictionary-style abbreviations, which are sort of unhelpful when
                # we can't expand them), and we also don't want to deal with texts
                # that are more than five words long.
                if (
                    text is not None and '.' not in text and
                    text.count(' ') <= 4 and valid_concept_name(text)
                ):
                    for head in headwords:
                        if len(senses) >= 2:
                            sensekey = '%d' % (sense_num + 1)
                            ja_concept = standardized_concept_uri('ja', head, pos, 'jmdict', sensekey)
                        else:
                            ja_concept = standardized_concept_uri('ja', head, pos)
                        other_concept = standardized_concept_uri(lang, text)
                        output_edge(out, '/r/Synonym', ja_concept, other_concept)

                        for context in contexts:
                            context_node = standardized_concept_uri('en', context)
                            output_edge(out, '/r/HasContext', ja_concept, context_node)


def output_edge(out, rel, subj_concept, obj_concept):
    """
    Write an edge to `out`, an instance of MsgpackStreamWriter.
    """
    edge = make_edge(rel, subj_concept, obj_concept,
                     dataset='/d/jmdict',
                     license=Licenses.cc_sharealike,
                     sources=[{'contributor': '/s/resource/jmdict/1.07'}],
                     weight=2.0)
    out.write(edge)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='XML copy of JMDict to read')
    parser.add_argument('output', help='msgpack-stream file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)


if __name__ == '__main__':
    main()

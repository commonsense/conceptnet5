from __future__ import unicode_literals
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri, standardize_text
from conceptnet5.edges import make_edge
from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter


# The language codes used by GlobalMind were idiosyncratic, and need to be
# converted to ISO-like codes by this dictionary instead of by the
# langcodes package. For example, 'cht' doesn't really mean Traditional
# Chinese, it means Cholón.
LANG_CODES = {
    'eng': 'en',
    'cht': 'zh-TW',
    'chs': 'zh-CN',
    'jpn': 'ja',
    'kor': 'ko',
    'spa': 'es',
}

LANG_NAMES = {
    'eng': 'English',
    'en': 'English',
    'cht': 'Traditional Chinese',
    'zh-tw': 'Traditional Chinese',
    'zh-TW': 'Traditional Chinese',
    'chs': 'Simplified Chinese',
    'zh-cn': 'Simplified Chinese',
    'zh-CN': 'Simplified Chinese',
    'zh': 'Chinese',
    'jpn': 'Japanese',
    'ja': 'Japanese',
    'kor': 'Korean',
    'ko': 'Korean',
    'spa': 'Spanish',
    'es': 'Spanish'
}

RELATION_MAP = {
    'ThematicKLine': 'RelatedTo',
    'EffectOf': 'Causes',
    'MotivationOf': 'MotivatedByGoal',
    'DesirousEffectOf': 'CausesDesire',
    'OnEvent': 'HasSubevent',
    'NotDesireOf': 'NotDesires',
    'FirstSubeventOf': 'HasFirstSubevent',
    'LastSubeventOf': 'HasLastSubevent',
    'SubeventOf': 'HasSubevent',
    'PrerequisiteEventOf': 'HasPrerequisite',
    'PropertyOf': 'HasProperty',
    'LocationOf': 'AtLocation',
    'DesireOf': 'Desires',
    'InstanceOf': 'IsA',
}


def get_lang(assertion):
    return assertion['start'].split('/')[2]


def build_from_dir(dirname, output_file):
    """
    Read a GlobalMind database exported in YAML files, translate
    it into ConceptNet 5 edges, and write those edges to disk using
    a MsgpackStreamWriter.
    """
    out = MsgpackStreamWriter(output_file)

    frames = {}
    for frame in read_json_stream(dirname + '/frames.jsons'):
        frames[frame['pk']] = frame['fields']

    usernames = {}
    for user in read_json_stream(dirname + '/users.jsons'):
        usernames[user['pk']] = user['fields']['username']

    assertions = {}
    for assertion in read_json_stream(dirname + '/assertions.jsons'):
        obj = assertion['fields']
        frame = frames[obj['frame']]
        frametext = frame['text']
        user_id = obj['author']
        username = standardize_text(usernames[user_id])
        user_source = "/s/contributor/globalmind/%s" % username

        source = {
            'contributor': user_source,
            'activity': "/s/activity/globalmind/assert"
        }

        lang = LANG_CODES[obj['lcode']]
        start = standardized_concept_uri(lang, obj['node1'])
        end = standardized_concept_uri(lang, obj['node2'])
        rel = '/r/' + RELATION_MAP.get(frame['relation'], frame['relation'])

        # fix messy english "around in"
        if ' around ' in frametext:
            if obj['node2'].startswith('in '):
                frametext = frametext.replace(' around ', ' in ')
                obj['node2'] = obj['node2'][3:]
            else:
                frametext = frametext.replace(' around ', ' near ')
                rel = '/r/LocatedNear'

        # fix more awkward English. I wonder how bad the other languages are.
        frametext = frametext.replace('hits your head', 'comes to mind')
        frametext = frametext.replace(': [node1], [node2]', ' [node1] and [node2]')

        node1 = u'[[' + obj['node1'] + u']]'
        node2 = u'[[' + obj['node2'] + u']]'
        surfaceText = frametext.replace('//', '')\
                               .replace('[node1]', node1)\
                               .replace('[node2]', node2)\
                               .replace('[nodo1]', node1)\
                               .replace('[nodo2]', node2)
        edge = make_edge(rel, start, end,
                         dataset='/d/globalmind',
                         license='/l/CC/By',
                         sources=[source],
                         surfaceText=surfaceText,
                         weight=0.5)

        # User IDs 2 and 3 contain data duplicated from OMCS.
        if user_id >= 4:
            out.write(edge)

        assertions[assertion['pk']] = edge

    for translation in read_json_stream(dirname + '/translations.jsons'):
        obj = translation['fields']
        assertion1 = assertions[obj['assertion1']]
        assertion2 = assertions[obj['assertion2']]
        start = assertion1['uri']
        end = assertion2['uri']
        rel = '/r/TranslationOf'
        text1 = assertion1['surfaceText'].replace('[[', '').replace(']]', '')
        text2 = assertion2['surfaceText'].replace('[[', '').replace(']]', '')
        lang1 = LANG_NAMES[get_lang(assertion1)]
        lang2 = LANG_NAMES[get_lang(assertion2)]
        surfaceText = u"[[%s]] in %s means [[%s]] in %s." % (text1, lang1, text2, lang2)
        user_id = obj['author']
        username = standardize_text(usernames[user_id])
        user_source = "/s/contributor/globalmind/%s" % username

        source = {
            'contributor': user_source,
            'activity': "/s/activity/globalmind/translate"
        }
        edge = make_edge(rel, start, end,
                         dataset='/d/globalmind',
                         license=Licenses.cc_attribution,
                         sources=[source],
                         surfaceText=surfaceText,
                         weight=0.5)
        out.write(edge)


# Entry point for testing
handle_file = build_from_dir


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help="Directory containing GlobalMind files")
    parser.add_argument('output', help='msgpack file to output to')
    args = parser.parse_args()
    build_from_dir(args.input_dir, args.output)


if __name__ == '__main__':
    main()

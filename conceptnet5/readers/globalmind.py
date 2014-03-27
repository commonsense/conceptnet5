from __future__ import unicode_literals
from conceptnet5.uri import Licenses
from conceptnet5.nodes import normalized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.json_stream import JSONStreamWriter

import yaml
import sys


# The language codes used by GlobalMind were idiosyncratic, and need to be
# converted to ISO-like codes by this dictionary instead of by the
# language_codes module. For example, 'cht' doesn't really mean Traditional
# Chinese, it means Cholón.
LANG_CODES = {
    'eng': 'en',
    'cht': 'zh_TW',
    'chs': 'zh_CN',
    'jpn': 'ja',
    'kor': 'ko',
    'spa': 'es',
}

LANG_NAMES = {
    'eng': 'English',
    'en': 'English',
    'cht': 'Traditional Chinese',
    'zh_TW': 'Traditional Chinese',
    'chs': 'Simplified Chinese',
    'zh_CN': 'Simplified Chinese',
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
}


def get_lang(assertion):
    return assertion['start'].split('/')[2]


def build_from_dir(dirname, output_file):
    """
    Read a GlobalMind database exported in YAML files, translate
    it into ConceptNet 5 edges, and write those edges to disk using
    a JSONStreamWriter.
    """
    out = JSONStreamWriter(output_file)
    userdata = yaml.load_all(open(dirname + '/GMUser.yaml'))
    users = {}

    for userinfo in userdata:
        users[userinfo['pk']] = userinfo

    frame_data = yaml.load_all(open(dirname + '/GMFrame.yaml'))
    frames = {}
    for frame in frame_data:
        frames[frame['pk']] = frame['fields']

    assertiondata = yaml.load_all(open(dirname + '/GMAssertion.yaml'))
    assertions = {}
    for assertion in assertiondata:
        obj = assertion['fields']
        frame = frames[obj['frame']]
        frametext = frame['text']
        userinfo = users[obj['author']]
        username = userinfo['fields']['username']

        # GlobalMind provides information about what country the user is from, which
        # we can preserve in the contributor URI.
        #
        # If I got to re-choose these URIs, I would distinguish usernames with
        # a country code from those without a country code by something more
        # than the number of slashes, and I would write the country code in
        # capital letters.
        userlocale = userinfo['fields']['ccode'].lower()
        if userlocale:
            user_source = "/s/contributor/globalmind/%s/%s" % (userlocale, username)
        else:
            user_source = "/s/contributor/globalmind/%s" % username

        sources = [
            user_source,
            "/s/activity/globalmind/assert"
        ]

        lang = LANG_CODES[obj['lcode']]
        start = normalized_concept_uri(lang, obj['node1'])
        end = normalized_concept_uri(lang, obj['node2'])
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
        surfaceText = frametext.replace('//', '').replace('[node1]', node1).replace('[node2]', node2)
        edge = make_edge(rel, start, end,
                         dataset='/d/globalmind',
                         license='/l/CC/By',
                         sources=sources,
                         surfaceText=surfaceText,
                         weight=1)
        out.write(edge)
        assertions[assertion['pk']] = edge

    translationdata = yaml.load_all(open(dirname + '/GMTranslation.yaml'))
    for translation in translationdata:
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
        userinfo = users[obj['author']]
        username = userinfo['fields']['username']

        userlocale = userinfo['fields']['ccode'].lower()
        if userlocale:
            user_source = "/s/contributor/globalmind/%s/%s" % (userlocale, username)
        else:
            user_source = "/s/contributor/globalmind/%s" % username

        sources = [
            user_source,
            "/s/activity/globalmind/translate"
        ]
        edge = make_edge(rel, start, end,
                         dataset='/d/globalmind',
                         license=Licenses.cc_attribution,
                         sources=sources,
                         surfaceText=surfaceText,
                         weight=1)
        out.write(edge)


# Entry point for testing
handle_file = build_from_dir


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help="Directory containing WordNet files")
    parser.add_argument('output', help='JSON-stream file to output to')
    args = parser.parse_args()
    build_from_dir(args.input_dir, args.output)


if __name__ == '__main__':
    main()


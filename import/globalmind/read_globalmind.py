from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import MultiWriter, make_edge

import yaml
userdata = yaml.load_all(open('./GMUser.yaml'))
users = {}
writer = MultiWriter('globalmind')

lang_codes = {
    'eng': 'en',
    'cht': 'zh_TW',
    'chs': 'zh_CN',
    'jpn': 'ja',
    'kor': 'ko',
    'spa': 'es',
}

lang_names = {
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

rel_change = {
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

for userinfo in userdata:
    users[userinfo['pk']] = userinfo

frame_data = yaml.load_all(open('GMFrame.yaml'))
frames = {}
for frame in frame_data:
    frames[frame['pk']] = frame['fields']

assertiondata = yaml.load_all(open('GMAssertion.yaml'))
assertions = {}
for assertion in assertiondata:
    obj = assertion['fields']
    frame = frames[obj['frame']]
    frametext = frame['text']
    userinfo = users[obj['author']]
    username = userinfo['fields']['username']
    userlocale = userinfo['fields']['ccode'].lower()
    if userlocale:
        userlocale += '/'
    sources = [
        "/s/contributor/globalmind/%s%s" % (userlocale, username),
        "/s/activity/globalmind/assert"
    ]
    lang = lang_codes[obj['lcode']]
    start = make_concept_uri(obj['node1'], lang)
    end = make_concept_uri(obj['node2'], lang)
    rel = '/r/'+rel_change.get(frame['relation'], frame['relation'])
    
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
    print surfaceText.encode('utf-8')
    assertions[assertion['pk']] = edge
    writer.write(edge)

def get_lang(assertion):
    return assertion['start'].split('/')[2]

translationdata = yaml.load_all(open('GMTranslation.yaml'))
for translation in translationdata:
    obj = translation['fields']
    assertion1 = assertions[obj['assertion1']]
    assertion2 = assertions[obj['assertion2']]
    start = assertion1['uri']
    end = assertion2['uri']
    rel = '/r/TranslationOf'
    text1 = assertion1['surfaceText'].replace('[[', '').replace(']]', '')
    text2 = assertion2['surfaceText'].replace('[[', '').replace(']]', '')
    lang1 = lang_names[get_lang(assertion1)]
    lang2 = lang_names[get_lang(assertion2)]
    surfaceText = u"[[%s]] in %s means [[%s]] in %s." % (text1, lang1, text2, lang2)
    userinfo = users[obj['author']]
    username = userinfo['fields']['username']
    userlocale = userinfo['fields']['ccode'].lower()
    if userlocale:
        userlocale += '/'
    sources = [
        "/s/contributor/globalmind/%s%s" % (userlocale, username),
        "/s/activity/globalmind/translate"
    ]
    edge = make_edge(rel, start, end,
                     dataset='/d/globalmind',
                     license='/l/CC/By',
                     sources=sources,
                     surfaceText=surfaceText,
                     weight=1)
    print surfaceText.encode('utf-8')
    writer.write(edge)

writer.close()
    

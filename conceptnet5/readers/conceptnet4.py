from conceptnet5.edges import make_edge
from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.nodes import standardized_concept_uri, valid_concept_name
from conceptnet5.uri import Licenses, join_uri
from wordfreq import simple_tokenize

"""
This script reads the ConceptNet 4 data out of the flat files in raw_data,
and builds ConceptNet 5 edges from the data.
"""


# bedume is a prolific OMCS contributor who seemed to go off the rails at some
# point, adding lots of highly correlated nonsense assertions. We need to
# filter them out without losing his informative statements.

BEDUME_FLAGGED_CONCEPTS = [
    'cute',
    'lost',
    'sewing',
    'brat',
    'working',
    'have sex',
    'shopping',
    'driving to work',
    'typing',
    'in jail',
    'jogging in park',
    'washing his car',
    'washing her car',
    'poor',
    'pulling weeds',
    'dancing',
    'sleeping',
    'pouting',
    'raking leaves',
    'washing her car',
    'chopping wood',
    'writing book',
    'shouting',
    'taking out garbage',
    'crying',
    'it',
    'running',
    'cooking',
    'late',
    'happy',
    'eating',
    'afraid',
    'voting',
    'it',
    'thief',
    'shoveling snow',
    'drinking',
    'drunk',
    'watching tv',
    'nut',
    'early',
    'well',
    'ill',
    'jogging',
    'dead',
    'naked',
    'playing cards',
    'sick',
    'painting',
    'reading',
    'hunter',
    'playing monopoly',
    'building new house',
    'riding horse',
    'playing in football game',
    'making love',
    'knitting',
    'going to take vacation',
    'fishing',
    'going to dentist',
    'going to store',
    'going to airport',
    'going to go to store',
    'kid',
    'computer',
    'stew',
    'taking walk',
    'tired',
    'new computer',
    'horn',
    'serving mealfish',
    'potatoe shed',
    'hunting',
    'crazy',
    'buying new car',
    'laughing',
    'intoxicated',
    'eating hamburger',
    'wok',
]
BEDUME_FLAGGED_PLACES = [
    'alaska',
    'kansa',
    'kansas',
    'utah',
    'austria',
    'delaware',
    'pennsylvania',
    'italy',
    'cuba',
    'norway',
    'idaho',
    'france',
    'utha',
    'mexico',
    'connecticut',
    'massachusetts',
    'montana',
    'wyoming',
    'every state',
    'new york',
    'maine',
    'suface of moon',
    'germany',
    'nebraska',
    'finland',
    'louisiana',
    'belgium',
    'morrocco',
    'ireland',
    'ceylon',
    'california',
    'oregon',
    'florida',
    'uraguay',
    'egypt',
    'maryland',
    'washington',
    'morocco',
    'south dakota',
    'tuscon',
    'panama',
    'alberta',
    'arizona',
    'texas',
    'new jersey',
    'colorado',
    'jamaica',
    'vermont',
    'nevada',
    'delawere',
    'hawaii',
    'minnesota',
    'tuscony',
    'costa rica',
    'south dakato',
    'south dakota',
    'china',
    'argentina',
    'venazuela',
    'honduras',
    'opera',
    'wisconsin',
    'great britain',
]
AROUND_PREPOSITIONS = ['in', 'on', 'at', 'under', 'near']

# Some specific relations were once added to ConceptNet that have no purpose
# for us anymore, especially ones connected with a project that was trying to
# understand how people describe pain.
#
# 'InheritsFrom' was an inference-related hack on ConceptNet 3 that was never
# supposed to make it into the actual database.

RELATIONS_TO_DROP = {
    '/r/HasPainIntensity',
    '/r/HasPainCharacter',
    '/r/InheritsFrom',
    '/r/SimilarSize',
}
CONTRIBUTOR_BLACKLIST = {
    '/s/contributor/omcs/brunogodoifred',
    '/s/contributor/omcs/thisislike',
    '/s/contributor/omcs/davidhere40',
    '/s/contributor/omcs/tdpoets',
    '/s/contributor/omcs/gcgirl',
    '/s/contributor/omcs/maratrea',
    '/s/contributor/omcs/poorrichard',
    '/s/contributor/omcs/fabian',
    '/s/contributor/omcs/coolio',
    '/s/contributor/omcs/wendybendy',
    '/s/contributor/omcs/kaaru',
    '/s/contributor/omcs/bntman',
    '/s/contributor/omcs/cyberguy',
    '/s/contributor/omcs/ddiblasi',
    '/s/contributor/omcs/glneumiller',
    '/s/contributor/omcs/imn8xtc',
    '/s/contributor/omcs/holyrobot',
    '/s/contributor/omcs/lbeckwith',
    '/s/contributor/omcs/maliki',
    '/s/contributor/omcs/sarcastro98',
    '/s/contributor/omcs/wellner',
    '/s/contributor/omcs/talshadar',
    '/s/contributor/omcs/mrt',
    '/s/contributor/omcs/humplik',
    '/s/contributor/omcs/mickh',
    '/s/contributor/omcs/visionsofkaos',
}
CONCEPT_BLACKLIST = {
    # Too vague
    '/c/en/',
    '/c/en/he',
    '/c/en/i',
    '/c/en/it',
    '/c/en/she',
    '/c/en/something',
    '/c/en/someone',
    '/c/en/that',
    '/c/en/there',
    '/c/en/they',
    '/c/en/this',
    '/c/en/you',
    '/c/en/often',
    '/c/en/sometimes',
    '/c/en/usually',
    '/c/en/if',
    '/c/en/when',
    '/c/en/whether',
    '/c/en/nothing',
    '/c/en/nobody',
    '/c/en/no_one',
    # OMCS users tended to give unfortunate, stereotyped answers when asked
    # about terms distinguished by their gender. As part of the de-biasing
    # effort, we should skip these. We can learn enough about 'man' and 'woman'
    # from dictionary definitions and from statements about 'person'.
    '/c/en/man',
    '/c/en/woman',
    '/c/en/boy',
    '/c/en/girl',
    '/c/en/boyfriend',
    '/c/en/girlfriend',
    '/c/en/brother',
    '/c/en/sister',
    '/c/en/mother',
    '/c/en/father',
    '/c/en/daughter',
    '/c/en/son',
    '/c/en/wife',
    '/c/en/husband',
}
ACTIVITY_BLACKLIST = {
    "20 Questions",
    "picture description",
    "response to picture",
    "response to diagram",
    "commons2_reject",
    "globalmind",
    "pycommons/question",
}

MORE_STOPWORDS = [
    'a',
    'an',
    'the',
    'be',
    'is',
    'are',
    'some',
    'any',
    'you',
    'me',
    'him',
    'it',
    'them',
    'i',
    'we',
    'she',
    'he',
    'they',
    'your',
    'my',
    'our',
    'his',
    'her',
    'its',
    'their',
    'this',
    'that',
    'these',
    'those',
    'something',
    'someone',
    'somebody',
    'anything',
    'anyone',
    "someone's",
    "something's",
    "anything's",
    "somebody's",
    "anyone's",
]


def can_skip(parts_dict):
    """
    Skip the kinds of data that we don't want to import from ConceptNet 4's
    database dump.

    The activity called 'testing' was actually collecting preliminary data for
    someone's dataset about subjective medical experiences. This data looks
    really out of place now.
    """
    lang = parts_dict['lang']
    if lang.startswith('zh'):
        # Chinese assertions from GlobalMind are not reliable enough. We'll get
        # Chinese from the `ptt_petgame` module instead.
        return True
    if lang == 'ja' and parts_dict["activity"] != 'nadya.jp':
        # Use Japanese data collected from nadya.jp, but not earlier attempts.
        return True
    if parts_dict["goodness"] <= 1:
        return True
    if 'spatial concept' in parts_dict["startText"]:
        return True
    if not parts_dict["startText"] or not parts_dict["endText"]:
        return True
    if len(parts_dict["startText"]) == 0 or len(parts_dict["endText"]) == 0:
        return True
    if lang == 'pt' and (
        len(parts_dict["startText"]) <= 2 or len(parts_dict["endText"]) <= 2
    ):
        return True
    if 'rubycommons' in parts_dict["activity"]:
        return True
    if 'Verbosity' in parts_dict["activity"]:
        return True
    if 'testing' in parts_dict["activity"]:
        return True
    if parts_dict["activity"] in ACTIVITY_BLACKLIST:
        return True
    if not (
        valid_concept_name(parts_dict["startText"])
        and valid_concept_name(parts_dict["endText"])
    ):
        return True
    return False


# TODO: this should be combined with 'can_skip'
def skip_assertion(source_dict, start, end):
    """
    Filter out assertions that we can tell will be unhelpful after we've
    extracted them.
    """
    if (
        lemmatize_uri(start) in CONCEPT_BLACKLIST
        or lemmatize_uri(end) in CONCEPT_BLACKLIST
    ):
        return True
    if source_dict['contributor'] in CONTRIBUTOR_BLACKLIST:
        return True
    if 'bedume' in source_dict['contributor']:
        for flagged in BEDUME_FLAGGED_CONCEPTS + BEDUME_FLAGGED_PLACES:
            check = '/' + flagged.replace(' ', '_')
            if start.endswith(check) or end.endswith(check):
                return True
    return False


def build_frame_text(parts_dict):
    """
    Make a ConceptNet 5 surfaceText out of the ConceptNet 4 assertion's
    frame and surface texts.
    """
    frame_text = parts_dict["frame_text"]
    # Mark frames where {2} precedes {1} with an asterisk.
    if frame_text.find('{1}') > frame_text.find('{2}'):
        frame_text = '*' + frame_text
    polarity = parts_dict["polarity"]

    # If this is a negative frame, then it should either have the negative
    # phrasing baked in, or (in English) the symbol {%} where we can insert
    # the word "not".
    if polarity > 0:
        frame_text = frame_text.replace('{%}', '')
    else:
        frame_text = frame_text.replace('{%}', 'not ')
    frame_text = frame_text.replace('{1}', '[[%s]]' % parts_dict["startText"]).replace(
        '{2}', '[[%s]]' % parts_dict["endText"]
    )
    return frame_text


def build_relation(parts_dict):
    """
    Update relation names to ConceptNet 5's names. Mostly we preserve the same
    names, but any instance of "ConceptuallyRelatedTo" becomes "RelatedTo".
    Statements with negative polarity get new negative relations.
    """
    relname = parts_dict["relname"]
    polarity = polarity = parts_dict["polarity"]
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = join_uri('/r', relname)
    else:
        relation = join_uri('/r', 'Not' + relname)

    return relation


def filtered_uri(lang, text):
    if lang == 'en':
        text = filter_stopwords(text)
    return standardized_concept_uri(lang, text)


def filter_stopwords(text):
    words = [word for word in simple_tokenize(text) if word not in MORE_STOPWORDS]
    text2 = ' '.join(words)
    if not text2:
        text2 = text
    return text2


def build_start(parts_dict):
    lang = parts_dict['lang']
    startText = parts_dict["startText"]
    start = filtered_uri(lang, startText)
    return start


def build_end(parts_dict):
    lang = parts_dict['lang']
    endText = parts_dict["endText"]
    end = filtered_uri(lang, endText)
    return end


def build_data_set(parts_dict):
    lang = parts_dict['lang']
    dataset = join_uri('/d/conceptnet/4', lang)
    return dataset


def standardize_username(username):
    """
    Convert usernames into a canonical form that can be used in URIs.

    If the username is an e-mail address, just keep the part before the @ sign.
    """
    name = username.strip('@').split('@')[0]
    name = '_'.join(simple_tokenize(name.replace('_', ' ')))
    return name


def build_sources(parts_dict, preposition_fix=False):
    """
    Create the 'source' information for an assertion.

    The output is a list of (conjunction, weight) tuples, where 'conjunction'
    is a list of sources that combined to produce this assertion. Later,
    inside the 'make_edge' function, these will be combined into an '/and'
    node.
    """
    creator_source = {}
    creator_node = join_uri(
        '/s/contributor/omcs', standardize_username(parts_dict["creator"])
    )
    creator_source['contributor'] = creator_node

    activity = parts_dict["activity"]
    activity = '_'.join(simple_tokenize(activity.replace('_', ' ')))
    activity_node = join_uri('/s/activity/omcs', activity)
    creator_source['activity'] = activity_node

    if preposition_fix:
        creator_source['process'] = '/s/process/preposition_fix'
    creator_source['weight'] = 1.
    sources = [creator_source]

    for vote in parts_dict["votes"]:
        username = vote[0]
        if username == parts_dict["creator"]:
            continue

        vote_int = vote[1]
        vote_source = {
            'contributor': join_uri(
                '/s/contributor/omcs', standardize_username(username)
            ),
            'activity': '/s/activity/omcs/vote',
            'weight': float(vote_int),
        }
        sources.append(vote_source)
    return sources


class CN4Builder(object):
    def __init__(self, weight=1.):
        """
        Create a builder for processing a source of ConceptNet-4-style
        assertions.

        The optional parameter provides a weight multiplier, which will modify
        the weight computed by `build_sources`. For example, this can be set
        lower than 1 for GWAPs, where we don't necessarily trust that every edge
        is a real assertion about common sense.
        """
        self.weight = weight

    def handle_assertion(self, parts_dict):
        """
        Process one assertion from ConceptNet 4, which appears in the input
        file as a dictionary.

        Use the 'raw' text -- the text that's not yet reduced to a normalized
        form -- so we can run ConceptNet 5's normalization on it instead.

        Each assertion becomes a number of ConceptNet 5 edges, which will
        probably be grouped together into an assertion again.
        """
        if can_skip(parts_dict):
            return

        # fix the result of some process that broke prepositions ages ago
        preposition_fix = False
        if '} around {' in parts_dict['frame_text']:
            for prep in AROUND_PREPOSITIONS:
                if parts_dict['endText'].startswith(prep + ' '):
                    parts_dict['endText'] = parts_dict['endText'][len(prep) + 1 :]
                    replacement = '} %s {' % prep
                    parts_dict['frame_text'] = parts_dict['frame_text'].replace(
                        '} around {', replacement
                    )
                    preposition_fix = True
                    break

        if can_skip(parts_dict):
            return

        # build the assertion
        frame_text = build_frame_text(parts_dict)
        relation = build_relation(parts_dict)
        start = build_start(parts_dict)
        end = build_end(parts_dict)
        dataset = build_data_set(parts_dict)
        weighted_sources = build_sources(parts_dict, preposition_fix)

        if relation in RELATIONS_TO_DROP:
            return

        if relation == '/r/DesireOf':
            # Fix an inconsistently-named relation from GlobalMind
            relation = '/r/Desires'

        for source_dict in weighted_sources:
            if not skip_assertion(source_dict, start, end):
                weight = source_dict.pop('weight')
                yield make_edge(
                    rel=relation,
                    start=start,
                    end=end,
                    dataset=dataset,
                    license=Licenses.cc_attribution,
                    sources=[source_dict],
                    surfaceText=frame_text,
                    # The edge weight is the weight computed by build_sources,
                    # times the multiplier set on this instance
                    weight=weight * self.weight,
                )

    def transform_file(self, input_filename, output_file):
        out = MsgpackStreamWriter(output_file)
        for obj in read_json_stream(input_filename):
            for new_obj in self.handle_assertion(obj):
                out.write(new_obj)


def handle_file(input_filename, output_file):
    builder = CN4Builder()
    builder.transform_file(input_filename, output_file)

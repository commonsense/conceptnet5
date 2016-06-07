from __future__ import print_function, unicode_literals, division
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.util.sounds_like import sounds_like_score
from collections import defaultdict
import re

# If any word in a clue matches one of these words, it is probably a bad
# common-sense assertion.
#
# Many of these represent violations of the use-mention distinction, such as
# "dog has three letters" instead of "dog has four legs". Others involve
# pronouns that refer to a previous clue or previous guess.
#
# I have no idea why the word 'mince' shows up in so many bad assertions, but
# it does.
BAD_CLUE_REGEX = re.compile(
    r'(^letter|^rhyme|^blank$|^words?$|^syllables?$|^spell|^tense$|^prefix'
    r'|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb'
    r'|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$'
    r'|^different|^this$|^that$|^these$|^those$|^mince$|^said$|^same$'
    r'|^delete|^remove|^add$|^drop$|^plus$|^more$|^less$|^combine$|^clue$'
    r'|^my|^your|^uppercase$|^capital|^previous$|^next$|^last$|^no$|^without$'
    r'|^sound| and$| or$| of$)'
)

# These are words we won't pull out of phrases in order to make individual
# assertions. The list is much more extensive than the three and a half
# stopwords that ConceptNet uses for English in general.
STOPWORDS = {
    'a', 'an', 'the', 'to', 'of', 'for', 'in', 'on', 'at', 'by', 'with', 'and',
    'or', 'far', 'near', 'away', 'from', 'thing', 'something', 'things', 'be',
    'is', 'are', 'was', 'were', 'as', 'so', 'get', 'i', 'me', 'you', 'it', 'he',
    'she', 'him', 'her', 'this', 'that', 'they', 'them', 'some', 'many', 'no',
    'one', 'all', 'either', 'both', 'er'
}


def handle_file(infile, outfile):
    count = 0
    outcomes = defaultdict(int)

    writer = MsgpackStreamWriter(outfile)

    for line in open(infile):
        parts = line.strip().split('\t')
        if not parts:
            outcomes['blank'] += 1
            continue

        # The first 5 columns of the Verbosity output file are:
        #
        #   left: the word being clued
        #   relation: the relation between the word and the clue that the
        #             clue-giver chose, in a form such as "it is part of"
        #   right: the one or two words used as the clue
        #   freq: the number of different times this clue was given
        #   orderscore: the average position in the list of clues
        #
        # 'orderscore' is a number from 0 to 999, representing the average
        # quantile of its position in the list of clues. (It's like a
        # percentile, except there are 1000 of them, not 100.)
        #
        # A clue that's always given first has an orderscore of 0. A clue
        # that always appears halfway through the list has an orderscore of
        # 500.
        #
        # This may seem like a strange thing to measure, and I didn't come up
        # with it, but it actually turns out to be somewhat informative.
        # A clue with an orderscore of 0 is probably a good common-sense
        # relation, representing the first thing that comes to mind. A clue
        # with a high order score may be a move of desperation after several
        # other clues have failed. It causes the guesser to get the answer
        # soon afterward, but perhaps because it's a "cheating" move. So,
        # low orderscores represent better common sense relations.
        left, relation, right, freq, orderscore = parts[:5]
        freq = int(freq)
        orderscore = int(orderscore)

        # Test each word
        flagged = False
        for rword in right.split():
            if BAD_CLUE_REGEX.match(rword):
                flagged = True
                break

        if flagged:
            outcomes['flag word'] += 1
            continue
        if len(right) < 3:
            outcomes['clue too short'] += 1
            continue
        if len(right.split()[-1]) == 1:
            outcomes['letter'] += 1
            continue

        # The Verbosity interface and gameplay did not particularly encourage
        # players to choose an appropriate relation. In practice, players seem
        # to have used them all interchangeably, except for the negative
        # relation "it is the opposite of", expressing /r/Antonym.
        #
        # Another way that players expressed negative relations was to use
        # 'not' as the first word of their clue; we make that into an instance
        # of /r/Antonym as well.
        #
        # In other cases, the relation is a positive relation, so we replace it
        # with the most general positive relation, /r/RelatedTo.
        rel = '/r/RelatedTo'
        reltext = 'is related to'
        if right.startswith('not '):
            rel = '/r/DistinctFrom'
            right = right[4:]
            reltext = 'is not'
        if relation == 'it is the opposite of':
            rel = '/r/Antonym'
            reltext = 'is the opposite of'

        # The "sounds-like score" determines whether this clue seems to be a
        # pun or rhyme, rather than an actual common-sense relationship. If
        # the sounds-like score is over 0.35, skip the assertion.
        sls = sounds_like_score(left, right)
        if sls > 0.35:
            outcomes['text similarity'] += 1
            continue

        # Calculate a score for the assertion:
        #
        #   - The number of times it's been used as a clue
        #   - ...with a linear penalty for a high sounds-like score
        #   - ...and a linear penalty for high orderscores
        #
        # The penalties are multiplicative factors from 0 to 1, which decrease
        # linearly as the relevant penalties increase. If a clue is given N
        # times, with a sounds-like score of 0 and an orderscore of 0, it will
        # get an overall score of 2N - 1. This is a formula we should probably
        # revisit.
        #
        # The weight is the score divided by 100. All divisions are floating
        # point, as defined by the __future__ import at the top of this module.
        score = (freq * 2 - 1) * (1 - sls) * (1 - orderscore / 1000)
        if score <= 1.:
            outcomes['low score'] += 1
            continue

        weight = score ** .5 / 10

        # If the clue on the right is a two-word phrase, we make additional
        # connections to both words individually. We label them with the
        # rule-based source '/s/process/split_words' to track that this
        # happened.
        rightwords = [right]
        if ' ' in right:
            morewords = [word for word in right.split(' ') if word not in STOPWORDS]
            rightwords.extend(morewords)

        for i, rightword in enumerate(rightwords):
            source = {
                'contributor': '/s/resource/verbosity'
            }
            if i > 0:
                source['process'] = '/s/process/split_words'

            # Build the natural-language-ish surface text for this clue
            text = '[[%s]] %s [[%s]]' % (left, reltext, rightword)

            count += 1
            outcomes['success'] += 1
            leftc = standardized_concept_uri('en', left)
            rightc = standardized_concept_uri('en', rightword)
            edge = make_edge(rel, leftc, rightc, dataset='/d/verbosity',
                             license=Licenses.cc_attribution,
                             sources=[source], surfaceText=text,
                             weight=weight)
            writer.write(edge)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Msgpack file of input')
    parser.add_argument('output', help='Msgpack file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)

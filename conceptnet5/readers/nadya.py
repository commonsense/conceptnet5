"""
Handle data that has been collected from nadya.jp, an online word game
created to collect data for ConceptNet, by Nihon Unisys and Dentsu.
"""
from conceptnet5.readers.conceptnet4 import CN4Builder
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter

# The nadya.jp data is distributed as a PostgreSQL database. The following
# command will extract a file in the form of 'nadya-2014.csv' from such a
# database:
#
#    SELECT
#        ra.id as cnet4_id,
#        ra.language_id as lang,
#        f.text as frame_text,
#        r.name as relname,
#        s1.text as start_text,
#        s2.text as end_text,
#        fr.value as freq,
#        v.vote,
#        u.username as creator,
#        u2.username as voter
#    FROM
#        conceptnet_rawassertion ra,
#        conceptnet_frame f,
#        conceptnet_assertion a,
#        auth_user u,
#        auth_user u2,
#        nl_frequency fr,
#        conceptnet_surfaceform s1,
#        conceptnet_surfaceform s2,
#        conceptnet_relation r,
#        votes v
#    WHERE
#        ra.frame_id=f.id and
#        ra.assertion_id=a.id and
#        ra.creator_id=u.id and
#        f.frequency_id = fr.id and
#        ra.surface1_id=s1.id and
#        ra.surface2_id=s2.id and
#        a.relation_id=r.id and
#        v.object_id=a.id and
#        v.user_id=u2.id and
#        u.email='a@nadya.jp' and
#        v.vote > 0 and
#        u.username != 'root';


def handle_line(line, builder):
    """
    Read one line of the tab-separated nadya.jp input, and yield 0 or 1
    ConceptNet edges that can be extracted from it.
    """
    parts = line.rstrip('\n').split('\t')
    (cnet4_id, lang, frame_text, relname, start_text, end_text,
     freq, vote, creator, voter) = parts
    if cnet4_id == 'cnet4_id':
        return

    # Convert numbers
    cnet4_id = int(cnet4_id)
    freq = int(freq)
    vote = int(vote)

    # Create the parts_dict that CN4Builder expects
    parts_dict = {
        'lang': lang,
        'polarity': freq,
        'cnet4_id': cnet4_id,
        'relname': relname,
        'frame_text': frame_text,
        'startText': start_text,
        'endText': end_text,
        # In the case of nadya.jp, it's not important to track the creator
        # separately from the voters -- they were all doing the same
        # thing.
        #
        # Each voter just shows up as the source of a separate
        # edge, which is what the CN4Builder ultimately does with the
        # votes anyway. The only reason the CN4Builder takes more complex
        # input is to handle weird edge cases.
        'creator': voter,
        'votes': [],
        'activity': 'nadya.jp',
        'goodness': 3
    }
    yield from builder.handle_assertion(parts_dict)


def handle_file(input_filename, output_file):
    builder = CN4Builder()
    out = MsgpackStreamWriter(output_file)
    for line in open(input_filename, encoding='utf-8'):
        # Get a line from the file
        for new_obj in handle_line(line, builder):
            out.write(new_obj)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='msgpack file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)


if __name__ == '__main__':
    main()


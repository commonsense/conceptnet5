from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
from metanl import japanese
from quick_reader import QuickReader
import sys
import os
import codecs
import re

JA = japanese.NoStopwordMeCabWrapper()

LICENSE = '/l/CC/By'

def can_skip(parts_dict):
    lang = parts_dict['lang']
    if lang != 'ja':
        return True
    if parts_dict["goodness"] < 1:
        return True

    activity = parts_dict["activity"]
    if 'rubycommons' in activity: 
        return True
    return False

def build_frame_text(parts_dict):
    frame_text = parts_dict["frame_text"]
    frame_text = frame_text.replace('{1}', '[[%s]]' % parts_dict["startText"]).replace('{2}', '[[%s]]' % parts_dict["endText"])
    return frame_text

def build_relation(parts_dict):
    polarity = parts_dict["polarity"]
    relname = parts_dict["relname"]
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = normalize_uri('/r/'+relname)
    else:
        relation = normalize_uri('/r/Not'+relname)
    return relation

def build_start(parts_dict):
    lang = parts_dict['lang']
    startText = ' '.join(JA.normalize_list(parts_dict["startText"]))
    start = make_concept_uri(startText, lang)
    return start

def build_end(parts_dict):
    lang = parts_dict['lang']
    endText = ' '.join(JA.normalize_list(parts_dict["endText"]))
    end = make_concept_uri(endText, lang)
    return end

def build_sources(parts_dict):
    score = parts_dict["score"]
    activity_node = normalize_uri(u'/s/site/nadya.jp')
    sources = [([activity_node], score/5.)]
    return sources

def build_data_set():
    return normalize_uri('/d/nadya.jp')


def extract_parts(flat_assertion):
    parts_dict = {}
    
    parts_dict["lang"] = re.findall('(?<=<lang>).*(?=</lang>)', flat_assertion)[0]
    parts_dict["creator"] = re.findall('(?<=<creator>).*(?=</creator>)', flat_assertion)[0]
    parts_dict["frame_id"] = int(re.findall('(?<=<frame_id>).*(?=</frame_id>)', flat_assertion)[0])
    parts_dict["startText"] = re.findall('(?<=<startText>).*(?=</startText>)', flat_assertion)[0]
    parts_dict["endText"] = re.findall('(?<=<endText>).*(?=</endText>)', flat_assertion)[0]
    parts_dict["activity"] = re.findall('(?<=<activity>).*(?=</activity>)', flat_assertion)[0]
    parts_dict["relname"] = re.findall('(?<=<relname>).*(?=</relname>)', flat_assertion)[0]
    parts_dict["polarity"] = float(re.findall('(?<=<polarity>).*(?=</polarity>)', flat_assertion)[0])
    parts_dict["goodness"] = float(re.findall('(?<=<goodness>).*(?=</goodness>)', flat_assertion)[0])
    parts_dict["frame_text"] = re.findall('(?<=<frame_text>).*(?=</frame_text>)', flat_assertion)[0]
    parts_dict["cnet4_id"] = int(re.findall('(?<=<cnet4_id>).*(?=</cnet4_id>)', flat_assertion)[0])
    parts_dict["score"] = float(re.findall('(?<=<score>).*(?=</score>)', flat_assertion)[0])
    raw_votes = re.findall('(?<=<votes>).*(?=</votes>)', flat_assertion)[0].split("<vote>")[1:]
    votes_list = []
    for raw_vote in raw_votes:
        raw_vote = raw_vote[:-7]
        parts = raw_vote.split(": ")
        vote_username = parts[0]
        vote_int = int(parts[1].split(" ")[0])
       
        votes_list.append((vote_username, vote_int))

    parts_dict["votes"] = votes_list

    return parts_dict



def handle_raw_flat_assertion(flat_assertion):
    try:
        parts_dict = extract_parts(flat_assertion)
        
        if can_skip(parts_dict):
            return []

        # build the assertion
        frame_text = build_frame_text(parts_dict)
        relation = build_relation(parts_dict)
        start = build_start(parts_dict)
        end = build_end(parts_dict)
        dataset = build_data_set()
        sources = build_sources(parts_dict)

        edges = []
        for source_list, weight in sources:
            if 'commons2_reject' in ' '.join(source_list):
                weight = -1
            
            else:
                edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                edges.append(edge)

        return edges
    except Exception:
        import traceback
        print "failed on flat_assertion: " + unicode(flat_assertion)
        traceback.print_exc()
        return []



def pull_lines_from_raw_flat_files(q):
    path = "./raw_data/"
    for filename in os.listdir(path):
        for line in codecs.open(path + filename, encoding='utf-8', errors='replace'):
            q.put(line)



if __name__ == '__main__':
    if "--build_from_flat" in sys.argv:
        quickReader = QuickReader("conceptnet_nadya", handle_raw_flat_assertion,pull_lines_from_raw_flat_files)
        quickReader.start()
   
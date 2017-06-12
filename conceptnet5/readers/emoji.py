import xml.etree.ElementTree as et
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.uri import Licenses, concept_uri

def is_sentence(text):
	if(' ' in text and not '|' in text):
		return True
	else:
		return False

def amt_words(text):
	return text.count('|')+1

def strip_words(text):
	res =  text.split('|')
	for i in range(len(res)):
		res[i] = res[i].replace(" ","")
	return res

def handle_file(input_file, output_file):
	tree = et.parse(input_file)
	root = tree.getroot()
	lang = root[0][1].attrib['type']
	out = MsgpackStreamWriter(output_file)
	for annotation in root[1]:
		if(not is_sentence(annotation.text)):
			rel = '/r/SymbolOf'
			start = '/c/mul/'+annotation.attrib['cp']
			dataset = '/d/emojis'
			license = Licenses.cc_attribution
			sources=[{'contributor': '/s/contributor/omcs/dev'}]
			for word in strip_words(annotation.text):
				end = concept_uri(lang,word)
				edge = make_edge(rel, start, end, dataset, license, sources)
				out.write(edge)
				

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='XML file of input')
    parser.add_argument('output', help='msgpack file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)

if __name__ == '__main__':
    main()


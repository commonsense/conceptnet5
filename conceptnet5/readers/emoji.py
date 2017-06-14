import xml.etree.ElementTree as et
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.formats.convert import msgpack_to_tab_separated
import click

def is_sentence(text):
    """
    there are a few instances where a sentence of
       multiple words is used to describe an emoji
       (not very helpful in our case) AS WELL AS single words or phrases,
       which are separated by '|'. Using this function, we can ignore
       the sentences because it's easier for conceptnet
       to handle phrases rather than nearly full sentences
    """
    return (' ' in text and '|' not in text)


def strip_words(text):
    """
    in instances where multiple words are used to describe emojis,
       they're separated by '|' delimiters. By removing the '|' characters,
       we also put all the separated words into an array which we can loop over
       and create edges for each one.
    """
    return text.split(' | ')


def handle_file(input_file, output_file):
    tree = et.parse(input_file)
    root = tree.getroot()
    lang = root[0][1].attrib['type']
    out = MsgpackStreamWriter(output_file)
    for annotation in root[1]:
        if(not is_sentence(annotation.text)):
            rel = '/r/SymbolOf'
            start = standardized_concept_uri("mul", annotation.attrib['cp'])
            dataset = '/d/emojis'
            license = Licenses.cc_attribution
            sources = [{'contributor': '/s/contributor/cldr/31'}]
            for word in strip_words(annotation.text):
                end = standardized_concept_uri(lang, word)
            edge = make_edge(rel, start, end, dataset, license, sources)
            out.write(edge)


@click.command()
#XML file of input
@click.argument('input', type=click.Path(readable=True, dir_okay=False))
#msgpack file to output to
@click.argument('output', type=click.Path(writable=True, dir_okay=False))
def cli(input,output):
  handle_file(input, output)


if __name__ == '__main__':
    cli()

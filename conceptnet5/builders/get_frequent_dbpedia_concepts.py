from conceptnet5.formats.semantic_web import parse_nquads
from conceptnet5.readers.dbpedia import translate_dbpedia_url
from collections import Counter
import click
import bz2


@click.command()
@click.argument('input_filename')
@click.argument('output_filename')
def get_frequent_dbpedia_concepts(input_filename, output_filename):
    """
    Read in a page_links_en.tql file. Output a list of concepts which have at least 100 Wikipedia links.
    """
    counter = Counter(
        translate_dbpedia_url(line[0]['url']) for line in parse_nquads(bz2.open(str(input_filename), 'rt')))

    with open(output_filename, 'w') as output_file:
        for concept, count in counter.most_common():
            if count >= 10:
                output_file.write(concept + '\n')
            else:
                break


if __name__ == '__main__':
    get_frequent_dbpedia_concepts()
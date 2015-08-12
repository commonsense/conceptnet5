import collections
import datetime
from os.path import exists
from itertools import chain

start_date = datetime.date.today().isoformat().replace('-', '')

def Dep(inputs, outputs, rule, params=None, use_existing=False):
    return {
        'inputs': inputs,
        'outputs': outputs,
        'rule': rule,
        'params': params,
        'use_existing': use_existing
    }


prefix = 'data/'
data_version = '5.4'

wiktionary_langs = ['en', 'de']
wiktionary_slices = 20
collate_count = 8

in_tar = {
    'wordnet':
        ['wordnet-synset.ttl', 'wordnet-glossary.ttl',
         'full/wordnet-wordsense-synset-relations.ttl',
         'wordnet-attribute.ttl', 'wordnet-causes.ttl',
         'wordnet-classifiedby.ttl', 'wordnet-entailment.ttl',
         'wordnet-hyponym.ttl', 'wordnet-instances.ttl',
         'wordnet-membermeronym.ttl', 'wordnet-partmeronym.ttl',
         'wordnet-sameverbgroupas.ttl', 'wordnet-similarity.ttl',
         'wordnet-substancemeronym.ttl', 'full/wordnet-antonym.ttl',
         'full/wordnet-derivationallyrelated.ttl',
         'full/wordnet-participleof.ttl',
         'full/wordnet-pertainsto.ttl',
         'full/wordnet-seealso.ttl'],

    'globalmind':
        ['GMFrame.yaml',
         'GMTranslation.yaml',
         'GMAssertion.yaml',
         'GMUser.yaml', ],

    'dbpedia':
        ['mappingbased_properties_en.nt',
         'instance_types_en.nt'],

    'jmdict':
        ['JMdict.xml'],

    'wiktionary':
        ['enwiktionary.xml',
         'dewiktionary.xml',
         'jawiktionary.xml'],

    'conceptnet4': ['conceptnet4_flat_%s.jsons' % i
                    for i in range(10)],

    'nadya': ['nadya-2014.csv'],
    'conceptnet_zh': ['conceptnet_zh_part%s.txt' % i
                      for i in range(1, 13)] + ['conceptnet_zh_api.txt'],

    'verbosity': ['verbosity.txt'],
    'umbel': ['umbel.nt'],

}

in_tar = {k: [prefix + 'raw/%s/%s' % (k, file) for file in v]
          for k, v in in_tar.items()}


def add_all_deps(deps):
    download(deps)
    untar(deps)

    parse_sw(deps)  # wordnet, umbel
    parse_standard(deps)  # jmdict, verbosity
    parse_globalmind(deps)
    parse_conceptnet4(deps)  # conceptnet4 conceptnet_zh
    extract_wiktionary(deps)
    parse_wiktionary(deps)
    parse_dbpedia(deps)

    msgpack_to_csv(deps)
    collate(deps)
    count_and_rank(deps)
    combine_assertions(deps)
    build_db(deps)

    msgpack_to_assoc(deps)
    stats(deps)

    build_vector_spaces(deps)
    upload(deps)


def download(deps):
    file = 'conceptnet5_raw_data_%s.tar.bz2' % data_version
    url = 'http://conceptnet5.media.mit.edu/downloads/v%s/' % data_version + file
    deps['download_tar'] = Dep(
        [],
        [prefix + 'conceptnet5_raw_data_%s.tar.bz2' % data_version],
        'download',
        {'prefix': prefix, 'url': url},
        use_existing=True
    )


def untar(deps):
    outputs = []
    for files in in_tar.values():
        outputs += files
    inputs = deps['download_tar']['outputs']
    deps['untar'] = Dep(inputs, outputs, 'extract_tar', {'prefix': prefix}, use_existing=True)


def parse_sw(deps):
    for type in ['wordnet', 'umbel']:
        deps['parse %s' % type] = Dep(
            in_tar[type],
            edge_output_list(type),
            'parse_sw',
            {
                'parser': type,
                'prefix': prefix + 'sw_map/',
                'dir': prefix + 'raw/' + type
            })


def parse_standard(deps):
    for type in ['jmdict', 'verbosity', 'nadya']:
        deps['parse %s' % type] = Dep(
            in_tar[type],
            edge_output_list(type),
            'parse',
            {'parser': type})


def parse_globalmind(deps):
    deps['parse globalmind'] = Dep(
        in_tar['globalmind'],
        edge_output_list('globalmind'),
        'parse_globalmind',
        {'parser': 'globalmind'})


def parse_dbpedia(deps):
    for file in in_tar['dbpedia']:

        if 'instance' in file:
            new = 'instances'
        else:
            new = 'properties'

        outputs = [
            prefix+'edges/dbpedia/%s.msgpack' % new,
            prefix+'sw_map/dbpedia_%s.nt' % new
        ]

        deps['parse dbpedia %s' % new] = Dep(
            file,
            outputs,
            'parse_dbpedia',
        )


def parse_conceptnet4(deps):
    for type in ['conceptnet4', 'conceptnet_zh']:
        for input in in_tar[type]:
            output = input.replace('jsons', 'msgpack')\
                .replace('txt', 'msgpack')\
                .replace('raw', 'edges')
            parser = 'conceptnet4' if not type.endswith('zh') else 'ptt_petgame'
            deps['parse %s %s' % (type, input)] = Dep(
                [input],
                [output],
                'parse',
                {'parser': parser})


def extract_wiktionary(deps):
    for lang in wiktionary_langs:
        input = prefix + 'raw/wiktionary/%swiktionary.xml' % lang
        path = prefix + 'extracted/wiktionary/%s/' % lang
        template = path + 'wiktionary_%02d.msgpack'

        outputs = [template % i for i in range(wiktionary_slices)]

        deps['extract %s wiktionary' % lang] = Dep(
            [input],
            outputs,
            'extract_wiktionary',
            {'lang': lang, 'dir': path})


def parse_wiktionary(deps):
    for lang in wiktionary_langs:
        for input in deps['extract %s wiktionary' % lang]['outputs']:
            index = input[-10:-8]

            deps['parse %s wiktionary %s' % (lang, index)] = Dep(
                [input],
                [input.replace('extracted', 'edges')],
                'parse_wiktionary',
                {'lang': lang})


def msgpack_to_csv(deps):
    new_deps = {}
    for k, v in deps.items():
        if not k.startswith('parse'):
            continue

        for input in v['outputs']:
            if not input.endswith('.msgpack'):
                continue

            new_deps['msgpack to csv %s' % input] = Dep(
                [input],
                [input.replace('msgpack', 'csv')],
                'msgpack_to_csv')

    deps.update(new_deps)


def collate(deps):
    inputs = []
    for k, v in deps.items():
        if k.startswith('msgpack to csv'):
            inputs += v['outputs']

    out_path = prefix + 'edges/split/'

    deps['collate'] = Dep(
        inputs,
        [out_path + 'edges_%02d.csv' % i
            for i in range(collate_count)],
        'collate',
        {'count': collate_count, 'dir': out_path}
    )


def count_and_rank(deps):
    for input in deps['collate']['outputs']:
        deps['count and rank %s' % input] = Dep(
            [input],
            [input.replace('split', 'sorted')],
            'count_and_rank')


def combine_assertions(deps):
    new_deps = {}
    for k, v in deps.items():
        if not k.startswith('count and rank'):
            continue
        input = v['outputs'][0]  # will only be a single element list

        new_deps['combine assertions %s' % input] = Dep(
            [input],
            [input.replace('edges/sorted', 'assertions')
                  .replace('edges', 'part')
                  .replace('csv', 'msgpack')
                  .replace('assertions_', 'part_')],
            'combine_assertions')

    deps.update(new_deps)


def msgpack_to_assoc(deps):
    new_deps = {}
    for k, v in deps.items():
        if not k.startswith('combine assertions'):
            continue

        input = v['outputs'][0]

        new_deps['msgpack to assoc %s' % input] = Dep(
            [input],
            [input.replace('msgpack', 'csv').replace('assertions', 'assoc')],
            'msgpack_to_assoc'
        )

    deps.update(new_deps)


def build_db(deps):
    inputs = []
    for k, v in deps.items():
        if not k.startswith('combine assertions'):
            continue
        inputs += v['outputs']

    deps['build db'] = Dep(
        inputs,
        [prefix + 'db/assertions.db'],
        'build_db',
        {'prefix': prefix})


def stats(deps):
    inputs = []
    for k, v in deps.items():
        if k.startswith('count and rank'):
            inputs += v['outputs']

    outputs = [prefix + 'stats/relations.txt']

    deps['relation stats'] = Dep(
        inputs,
        outputs,
        'relation_stats'
    )

    dataset_outputs = []

    for side, fields in [('left', '3,9'), ('right', '4,9')]:
        output = prefix + 'stats/concepts_%s_datasets.txt' % side
        dataset_outputs.append(output)

        deps['dataset stats %s' % side] = Dep(
            inputs,
            [output],
            'dataset_stats',
            {'fields': fields}
        )

    deps['dataset vs language'] = Dep(
        dataset_outputs,
        [prefix + 'stats/dataset_vs_language.txt'],
        'dataset_vs_language_stats'
    )

    deps['more stats'] = Dep(
        inputs,
        [prefix + 'stats/morestats.txt'],
        'more_stats'
    )

def build_vector_spaces(deps):
    vecs = []
    for csv in outputs_where(deps, lambda x: x.startswith('data/assoc/part_0') and x.endswith('.csv')):
        output = csv.replace('.csv', '').replace('/assoc/', '/assoc/subspaces/')
        vecs.append(output)
        deps['assoc to vector %s'%output] = Dep(
            [csv],
            [output],
            'build_assoc'
        )

    deps['merge vector spaces'] = Dep(
        vecs,
        ['data/assoc/subspaces/merged_filtered'],
        'merge_assoc'
    )

def upload(deps):
    uploads = []
    msgpacks = outputs_where(deps,
                             lambda x: x.startswith('data/assertions/') and
                                       x.endswith('.msgpack'))

    for msgpack in msgpacks:
        deps['to jsons %s'%msgpack] = Dep(
            [msgpack],
            [msgpack.replace('.msgpack', '.jsons')],
            'msgpack_to_json'
        )

        deps['to csv %s'%msgpack] = Dep(
            [msgpack],
            [msgpack.replace('.msgpack', '.csv')],
            'msgpack_to_csv'
        )

    for output, inputs in [
        ('raw_data', list(chain(*in_tar.values()))),
        ('flat_msgpack', msgpacks),
        ('flat_json', outputs_where(deps, lambda x: x.startswith('data/assertions/') and x.endswith('.jsons'))),
        ('flat_csv', outputs_where(deps, lambda x: x.startswith('data/assertions/') and x.endswith('.csv'))),
        ('db', deps['build db']['outputs'] + msgpacks),
        ('vector_space', deps['merge vector spaces']['outputs'])
    ]:
        output = prefix + 'dist/' + start_date + '/conceptnet5_' + output + '_5.4.tar.bz2'
        uploads.append(output)
        deps['upload '+output] = Dep(
            inputs,
            [output],
            'compress_tar'
        )

    deps['upload'] = Dep(
        uploads,
        ['UPLOAD'],
        'upload'
    )

def outputs_where(deps, where):
    out = set()
    for v in deps.values():
        out.update(output for output in v['outputs'] if where(output))
    return list(out)

def edge_output_list(type):
    return [prefix + 'edges/%s/%s.msgpack' % (type, type)]


def to_ninja(rules, deps, only=None):
    lines = [rules]
    for name, dep in deps.items():
        if only is not None and not only(name):
            continue
        add_dep(lines, **dep)
    return "\n".join(lines)


def add_dep(lines, rule, inputs, outputs, extra=None, params=None, use_existing=False):
    if isinstance(outputs, list):
        outputs = ' '.join(outputs)
    if isinstance(inputs, list):
        inputs = ' '.join(inputs)
    if extra:
        if isinstance(extra, list):
            extra = ' '.join(extra)
        extrastr = ' | ' + extra
    else:
        extrastr = ''

    if use_existing and all(exists(output) for output in outputs.split()):
        return

    build_rule = "build {outputs}: {rule} {inputs}{extra}".format(
        outputs=outputs, rule=rule, inputs=inputs, extra=extrastr
    )
    lines.append(build_rule)
    if params:
        for key, val in params.items():
            lines.append("  {key} = {val}".format(key=key, val=val))
    lines.append("")


class NoOverrideDict(collections.OrderedDict):
    """
    NoOverrideDict prevents values from being changed once set.

    This prevents functions from overriding existing dependencies.
    """

    def __setitem__(self, key, val):
        if super().__contains__(key):
            raise ValueError()
        return super().__setitem__(key, val)


def main():
    deps = NoOverrideDict()
    add_all_deps(deps)
    ninja = to_ninja(open('rules.ninja').read(), deps)
    print(ninja, file=open('build.ninja', mode='w'))


if __name__ == '__main__':
    main()

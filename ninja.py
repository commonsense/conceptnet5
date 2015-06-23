def Dep(inputs, outputs, rule, params=None):
    return {
        'inputs': inputs,
        'outputs': outputs,
        'rule': rule,
        'params': params,
    }

prefix = 'data/'
version = '5.3'

wiktionary_langs = ['en', 'de', 'ja']
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
         'interlanguage_links_en.nt',
         'instance_types_en.nt', ],

    'jmdict':
        ['JMdict.xml'],

    'wiktionary':
        ['enwiktionary.xml',
         'dewiktionary.xml',
         'jawiktionary.xml', ],

    'conceptnet4': ['conceptnet4_flat_%s.jsons' % i
                    for i in range(10)],

    'conceptnet4_nadya': ['conceptnet4_nadya_flat_%s.jsons' % i
                          for i in range(10)],

    'conceptnet_zh': ['rconceptnet_zh_part%s.txt' % i
                      for i in range(13)],

    'verbosity': ['raw/verbosity/verbosity.txt', ],
    'umbel': ['raw/umbel/umbel.nt', ],

}

in_tar = {k: [prefix + 'raw/%s/%s' % (k, file) for file in v]
          for k, v in in_tar.items()}


def add_all_deps(deps):
    download(deps)
    untar(deps)
    parse_sw(deps)  # wordnet, umbel
    parse_standard(deps)  # globalmind, jmdict, verbosity
    parse_conceptnet4(deps)  # conceptnet4 conceptnet4_nadya conceptnet_zh
    extract_wiktionary(deps)
    parse_wiktionary(deps)
    msgpack_to_csv(deps)
    collate(deps)
    count_and_rank(deps)
    combine_assertions(deps)
    build_db(deps)


def download(deps):
    output = prefix + 'conceptnet5_raw_data_%s.tar.bz2' % version
    url = 'http://conceptnet5.media.mit.edu/downloads/v%s/' % version + output
    deps['download_tar'] = Dep(
        [],
        prefix + 'conceptnet5_raw_data_%s.tar.bz2' % version,
        'download',
        {'prefix': prefix, 'url': url}
    )


def untar(deps):
    outputs = []
    for files in in_tar.values():
        outputs += files
    input = deps['download_tar']['outputs']
    deps['untar'] = Dep([input], outputs, 'extract_tar', {'prefix': prefix})


def parse_sw(deps):
    for type in ['wordnet', 'umbel']:
        deps['parse %s' % type] = Dep(
            in_tar[type],
            edge_output_str(type),
            'parse_sw',
            {
                'parser': type,
                'prefix': prefix + 'sw_map',
                'dir': prefix + 'raw/' + type
            })


def parse_standard(deps):
    for type in ['globalmind', 'jmdict', 'verbosity']:
        deps['parse %s' % type] = Dep(
            in_tar[type],
            edge_output_str(type),
            'parse',
            {'parser': type})


def parse_conceptnet4(deps):
    for type in ['conceptnet4', 'conceptnet4_nadya', 'conceptnet_zh']:
        for input in in_tar[type]:
            output = input.replace('jsons', 'msgpack')\
                .replace('txt', 'msgpack')\
                .replace('raw', 'edges')
            parser = type if not type.endswith('zh') else 'ptt_petgame'
            deps['parse %s' % type] = Dep(
                [input],
                [output],
                'parse',
                {'parser': parser})


def extract_wiktionary(deps):
    for lang in wiktionary_langs:
        input = prefix + 'raw/wiktionary/%swiktionary.xml' % lang
        template = prefix + 'extracted/wiktionary/%s/wiktionary_%02d.msgpack'

        outputs = [template % (lang, i)
                   for i in range(wiktionary_slices)]

        deps['extract %s wiktionary' % lang] = Dep(
            [input],
            outputs,
            'extract_wiktionary',
            {'lang': lang})


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

    deps['collate'] = Dep(
        inputs,
        [prefix + 'edges/split/edges_%02d.csv' % i
            for i in range(collate_count)],
        'collate',
        {'count': collate_count}
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
            [input.replace('edges', 'assertions').replace('csv', 'msgpack')],
            'combine_assertions')

    deps.update(new_deps)


def build_db(deps):
    inputs = []
    for k, v in deps.items():
        if not k.startswith('combine assertions'):
            continue
        inputs += v['outputs']
    output = prefix + 'db/assertions.db'

    deps['build db'] = Dep(
        inputs,
        [output],
        'build_db'
    )


def edge_output_str(type):
    return [prefix + 'edges/%s/%s.msgpack' % (type, type)]


def to_ninja(rules, deps):
    lines = [rules]
    for dep in deps.values():
        add_dep(lines, **dep)
    return "\n".join(lines)


def add_dep(lines, rule, inputs, outputs, extra=None, params=None):
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
    build_rule = "build {outputs}: {rule} {inputs}{extra}".format(
        outputs=outputs, rule=rule, inputs=inputs, extra=extrastr
    )
    lines.append(build_rule)
    if params:
        for key, val in params.items():
            lines.append("  {key} = {val}".format(key=key, val=val))
    lines.append("")


def main():
    deps = {}
    add_all_deps(deps)
    ninja = to_ninja(open('rules.ninja').read(), deps)
    print(ninja, file=open('build.ninja', mode='w'))


if __name__ == '__main__':
    main()

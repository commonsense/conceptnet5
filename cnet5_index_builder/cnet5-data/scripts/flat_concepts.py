import codecs
out = codecs.open('data/flat/concepts.txt', 'w', encoding='utf-8')
for line in codecs.open('data/flat/ALL.csv', encoding='utf-8'):
    id, rel, start, end = line.split('\t')[:4]
    print >> out, rel
    print >> out, start
    print >> out, end

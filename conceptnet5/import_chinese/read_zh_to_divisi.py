from conceptnet.models import *
import divisi2
import os
import codecs

sparse_pieces = []
for filename in os.listdir('.'):
    if filename.startswith('conceptnet_zh_'):
        for line in codecs.open(filename, encoding='utf-8', errors='replace'):
            line = line.strip()
            if line:
                parts = line.split(', ')
                user, frame_id, concept1, concept2 = parts
                relation = Frame.objects.get(id=int(frame_id)).relation
                left_feature = u"%s\\%s" % (concept1, relation)
                right_feature = u"%s/%s" % (relation, concept2)

                sparse_pieces.append((1, concept1, right_feature))
                sparse_pieces.append((1, concept2, left_feature))

matrix = divisi2.make_sparse(sparse_pieces)
divisi2.save(matrix, 'feature_matrix_zh.smat')

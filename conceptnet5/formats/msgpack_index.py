import kyotocabinet
import msgpack
import struct
import mmap
import os
from conceptnet5.uri import uri_prefixes


class ConceptNetIndex:
    """
    This object allows looking up ConceptNet assertions by the values they
    contain (such as the URIs of nodes that they connect).
    """
    def __init__(self, index_filename, msgpack_filename):
        self.db = kyotocabinet.DB()
        if not self.db.open(index_filename, self.db.OREADER):
            raise IOError("Couldn't open index file %r" % index_filename)

        self.assertion_file = self._mmap_file(msgpack_filename)
    
    def _mmap_file(self, path):
        fileobj = open(path, 'rb')
        file_mmap = mmap.mmap(fileobj.fileno(), 0, prot=mmap.PROT_READ)
        return file_mmap

    def get_with_index(self, key):
        got = self.db.get(key)
        if got is not None:
            return self._iter_edges(got)

    def _iter_edges(self, value):
        for pos in range(0, len(value), 12):
            data = value[pos:pos + 12]
            invweight, offset = struct.unpack('>fQ', data)
            edge = self._get_edge(offset)
            yield edge

    def get_with_prefix(self, prefix):
        bprefix = prefix.encode('utf-8')
        try:
            cursor = self.db.cursor()
            if not cursor.jump(bprefix):
                return

            while True:
                key, value = cursor.get(True)
                if not key.startswith(bprefix):
                    return
                if key == bprefix or key.startswith(bprefix + b'/'):
                    yield from self._iter_edges(value)
        finally:
            cursor.disable()

    def _get_edge(self, offset):
        self.assertion_file.seek(offset)
        unpacker = msgpack.Unpacker(self.assertion_file, encoding='utf-8')
        return unpacker.unpack()

    def close(self):
        self.db.close()
        self.assertion_file.close()

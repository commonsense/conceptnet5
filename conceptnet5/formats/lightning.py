import lmdb
import msgpack
import struct
import mmap
import os
from conceptnet5.uri import uri_prefixes


class ConceptNetLMDB:
    def __init__(self, dirname, edge_dirname, readonly=True):
        self.env = lmdb.Environment(
            dirname,
            map_size=100 << 30,  # allow the database to grow to 100 GB
            readonly=readonly,
            writemap=True,
            map_async=True,
            max_dbs=5
        )
        self.edge_dir = edge_dirname
        self.index_db = self.env.open_db(b'index', dupsort=True)
        self.readonly = readonly
        self.open_file_cache = {}

    def write_transaction(self):
        if self.readonly:
            raise RuntimeError("This LMDB is read-only")
        txn = self.env.begin(write=True)
        return txn

    def read_transaction(self, db=None):
        return self.env.begin(write=False, db=db)

    def store_indices(self, txn, edge, filenum, offset):
        weight = edge['weight']
        for field in ('uri', 'rel', 'start', 'end', 'dataset'):
            self.index_prefixes(txn, edge[field], filenum, offset, weight)
        for source in edge['sources']:
            self.index_prefixes(txn, source, filenum, offset, weight)
        for feature in edge['features']:
            self.store_index_value(txn, feature, filenum, offset, weight)

    def index_prefixes(self, txn, uri, filenum, offset, weight):
        for pref in uri_prefixes(uri):
            self.store_index_value(txn, pref, filenum, offset, weight)

    def store_index_value(self, txn, key, filenum, offset, weight):
        if isinstance(key, str):
            key = key.encode('utf-8')
        if len(key) == 0 or len(key) >= 500:
            return
        value = struct.pack('>fbi', 1.0 / weight, filenum, offset)
        txn.put(
            key, value, dupdata=True, db=self.index_db
        )

    def get_with_index(self, key, limit=100):
        with self.read_transaction(self.index_db) as txn:
            cursor = txn.cursor()
            found = cursor.set_key(key.encode('utf-8'))
            if found:
                edges = []
                for value in cursor.iternext_dup():
                    edge = self._get_edge(value)
                    edges.append(edge)
                    if len(edges) >= limit:
                        break
                return edges
            else:
                return []

    def store_edge(self, txn, edge):
        key = edge['id'].encode('utf-8')
        txn.put(key, msgpack.dumps(edge))

    def get_file(self, filenum):
        if filenum in self.open_file_cache:
            return self.open_file_cache[filenum]
        else:
            filename = 'part_%02d.msgpack' % filenum
            path = os.path.join(self.edge_dir, filename)
            size = os.path.getsize(path)
            fileobj = open(path, 'rb')
            file_mmap = mmap.mmap(fileobj.fileno(), 0, prot=mmap.PROT_READ)
            self.open_file_cache[filenum] = file_mmap
            return fileobj

    def _get_edge_from_file(self, filenum, offset):
        fileobj = self.get_file(filenum)
        fileobj.seek(offset)
        unpacker = msgpack.Unpacker(fileobj, encoding='utf-8')
        return unpacker.unpack()

    def _get_edge(self, pointer):
        weight, filenum, offset = struct.unpack('>fbi', pointer)
        return self._get_edge_from_file(filenum, offset)

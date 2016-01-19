import lmdb
import msgpack
import struct
from conceptnet5.uri import uri_prefixes


class ConceptNetLMDB:
    def __init__(self, dirname, readonly=True):
        self.env = lmdb.Environment(
            dirname,
            map_size=100 << 30,  # allow the database to grow to 100 GB
            readonly=readonly,
            writemap=True,
            map_async=True,
            max_dbs=5
        )
        self.index_db = self.env.open_db(b'index', dupsort=True)
        self.edge_db = self.env.open_db(b'edges')
        self.node_db = self.env.open_db(b'nodes')
        self.readonly = readonly

    def write_transaction(self):
        if self.readonly:
            raise RuntimeError("This LMDB is read-only")
        txn = self.env.begin(write=True)
        return txn

    def read_transaction(self, db=None):
        return self.env.begin(write=False, db=db)

    def store_indices(self, txn, edge):
        pointer = edge['id']
        weight = edge['weight']
        for field in ('uri', 'rel', 'start', 'end', 'dataset'):
            self.index_prefixes(txn, edge[field], pointer, weight)
        for source in edge['sources']:
            self.index_prefixes(txn, source, pointer, weight)
        for feature in edge['features']:
            self.store_index_value(txn, feature, pointer, weight)

    def index_prefixes(self, txn, uri, pointer, weight):
        for pref in uri_prefixes(uri):
            self.store_index_value(txn, pref, pointer, weight)

    def store_index_value(self, txn, key, pointer, weight):
        if isinstance(key, str):
            key = key.encode('utf-8')
        weight_bytes = struct.pack('>f', 1.0 / weight)
        value = weight_bytes + pointer.encode('utf-8')
        txn.put(
            key, value, dupdata=True, db=self.index_db
        )

    def get_with_index(self, key, limit=100):
        txn = self.read_transaction(self.index_db)
        cursor = txn.cursor()
        found = cursor.set_key(key.encode('utf-8'))
        if found:
            edges = []
            for value in cursor.iternext_dup():
                pointer = value[4:]
                edge = self.get_edge(pointer, txn=txn)
                edges.append(edge)
                if len(edges) >= limit:
                    break
            return edges
        else:
            return []

    def store_edge(self, txn, edge):
        key = edge['id'].encode('utf-8')
        txn.put(key, msgpack.dumps(edge))

    def get_edge(self, key, txn=None):
        if isinstance(key, str):
            key = key.encode('utf-8')
        if txn is None:
            txn = self.read_transaction(self.edge_db)
        return txn.get(key)

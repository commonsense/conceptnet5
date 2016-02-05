import msgpack
import struct
import mmap
import mmh3

HEADER_SIZE = 16
ENTRY_SIZE = 16


class HashTableIndex:
    def __init__(self, filename):
        self.data = open(filename, 'rb')
        header = self.data.read(4)
        assert header[:3] == b'CN5'
        self._hash_width = header[3]
        _ = self.data.read(4)
        self._table_ptr = struct.unpack('<Q', self.data.read(8))[0]

    def _hash_bytes(self, key):
        return struct.pack('<q', mmh3.hash64(key)[0])

    def _bucket(self, hbytes):
        val = struct.unpack('<Q', hbytes)[0]
        return val >> (64 - self._hash_width)

    def lookup(self, key):
        hbytes = self._hash_bytes(key)
        bucket = self._bucket(hbytes)

        loc = self._table_ptr + ENTRY_SIZE * bucket
        self.data.seek(loc)
        zero = bytes(8)
        while True:
            data = self.data.read(16)
            if not data:
                return []
            if data[:8] == zero:
                return []
            elif data[:8] == hbytes:
                ptr = struct.unpack('<Q', data[8:])[0]
                return self._unpack_values(ptr)

    def _unpack_values(self, ptr):
        self.data.seek(ptr)
        unpacker = msgpack.Unpacker(self.data, encoding='utf-8')
        values = unpacker.unpack()
        assert isinstance(values, list)
        return values

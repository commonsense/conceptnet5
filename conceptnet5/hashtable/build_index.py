import msgpack
import math
import itertools
import struct
import tempfile
import json


def hash_table_bits(num_entries):
    """
    Use enough bits of the hash that the hash table will be between
    35% and 71% full.
    """
    if num_entries == 0:
        return 0
    nbits = round(math.log(num_entries, 2)) + 1
    return nbits


HEADER_SIZE = 8
ENTRY_SIZE = 16
BUFFER_SIZE = 65536


def build_index(preindex_filename, hashtable_filename, hash_width):
    # hash_width = hash_table_bits(num_values)
    print("Using %d bits for hashtable" % hash_width)
    with open(hashtable_filename, 'wb') as hfile:
        # Write the header
        hfile.write(b'\xf0\x9f\xa5\x81\x00\x00')
        hfile.write(bytes([hash_width, 0]))
        values_start = HEADER_SIZE + (1 << hash_width) * ENTRY_SIZE

        with tempfile.TemporaryFile(prefix='conceptnet5.hashtable.') as vfile:
            with open(preindex_filename, 'r', encoding='utf-8') as preindex:
                groups = itertools.groupby(
                    preindex, key=_make_bucket_function(hash_width)
                )
                for bucket, lines in groups:
                    hfile_pos = hfile.tell()
                    target_pos = HEADER_SIZE + bucket * ENTRY_SIZE
                    if target_pos > hfile_pos:
                        hfile.seek(target_pos)
                    
                    keygroups = itertools.groupby(
                        lines, key=_extract_keyhash
                    )
                    for keyhash, lines2 in keygroups:
                        values = []
                        for line in lines2:
                            _, _, value = line.rstrip().split('\t')
                            values.append(json.loads(value))
                        encoded = msgpack.dumps(values, use_bin_type=True)
                        vpos = values_start + vfile.tell()

                        record = struct.pack('<QQ', int(keyhash, 16), vpos)
                        hfile.write(record)
                        vfile.write(encoded)

            hfile.seek(values_start)
            vfile.seek(0)
            while True:
                read = vfile.read(BUFFER_SIZE)
                if len(read) == 0:
                    break
                hfile.write(read)


def _make_bucket_function(nbits):
    def _hash_bucket(line):
        keyhash = line.split('\t')[0]
        # keynum is a 64-bit unsigned number
        keynum = int(keyhash, 16)
        return keynum >> (64 - nbits)
    return _hash_bucket


def _extract_keyhash(line):
    return line.split('\t')[0]


from .index import HEADER_SIZE, ENTRY_SIZE
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


BUFFER_SIZE = 65536


def copy_data(input_file, output_file):
    while True:
        read = input_file.read(BUFFER_SIZE)
        if len(read) == 0:
            break
        output_file.write(read)


def build_index(preindex_filename, hashtable_filename, hash_width):
    with tempfile.TemporaryFile(prefix='conceptnet5.values.') as vfile:
        with tempfile.TemporaryFile(prefix='conceptnet5.hashtable.') as hfile:
            with open(preindex_filename, 'r', encoding='utf-8') as preindex:
                groups = itertools.groupby(
                    preindex, key=_make_bucket_function(hash_width)
                )
                for bucket, lines in groups:
                    hfile_pos = hfile.tell()
                    target_pos = bucket * ENTRY_SIZE
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
                        vpos = vfile.tell() + HEADER_SIZE
                        record = struct.pack('<QQ', int(keyhash, 16), vpos)
                        hfile.write(record)
                        vfile.write(encoded)

            values_size = vfile.tell()

            hfile.seek(0)
            vfile.seek(0)
            with open(hashtable_filename, 'wb') as outfile:
                # Header: "CN5" in ASCII, followed by the hash width, and four
                # unused bytes that we might find a need for in the future
                outfile.write(b'CN5')
                outfile.write(bytes([hash_width, 0, 0, 0, 0]))

                # 8-byte pointer to the start of the hashtable
                outfile.write(struct.pack('<Q', values_size + HEADER_SIZE))

                # Value data
                copy_data(vfile, outfile)

                # Hashtable data
                copy_data(hfile, outfile)


def _make_bucket_function(nbits):
    def _hash_bucket(line):
        keyhash = line.split('\t')[0]
        # keynum is a 64-bit unsigned number
        keynum = int(keyhash, 16)
        return keynum >> (64 - nbits)
    return _hash_bucket


def _extract_keyhash(line):
    return line.split('\t')[0]

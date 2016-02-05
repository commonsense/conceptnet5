import mmh3
import struct
import json
import binascii
import sys


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'),
                      indent=None)


def preindex_data(input_pairs, output_stream=sys.stdout):
    """
    `input_pairs` is a list of (key, value) pairs. The key must be a string,
    and the value must be encodable as JSON.

    `output_stream` is an open file that accepts Unicode text (possibly
    stdout).
    """
    for key, weight, value in input_pairs:
        if weight > 0:
            keyhash = binascii.b2a_hex(struct.pack('>q', mmh3.hash64(key)[0])).decode('ascii')
            enc_weight = binascii.b2a_hex(struct.pack('>f', 1.0 / weight)).decode('ascii')
            enc_value = compact_json(value)
            print('{}\t{}\t{}'.format(keyhash, enc_weight, enc_value),
                  file=output_stream)

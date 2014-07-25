from __future__ import unicode_literals
import msgpack


class MsgpackStreamWriter(object):
    """
    Write a stream of data in msgpack stream format.
    """

    def __init__(self, filename_or_stream):
        if hasattr(filename_or_stream, 'write'):
            self.stream = filename_or_stream
        else:
            self.stream = open(filename_or_stream, 'wb')
        self.packer = msgpack.Packer()

    def write(self, obj):
        self.stream.write(self.packer.pack(obj))

    def close(self):
        self.stream.close()


def read_msgpack_stream(filename_or_stream, offsets=False):
    if hasattr(filename_or_stream, 'read'):
        stream = filename_or_stream
    else:
        stream = open(filename_or_stream, 'rb')

    unpacker = msgpack.Unpacker(stream)
    for value in unpacker:
        if offsets:
            yield (value, stream.tell())
        else:
            yield value

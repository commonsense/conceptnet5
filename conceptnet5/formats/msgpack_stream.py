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
        self.packer = msgpack.Packer(encoding='utf-8')

    def write(self, obj):
        self.stream.write(self.packer.pack(obj))

    def close(self):
        self.stream.close()


def read_msgpack_stream(filename_or_stream, offsets=False):
    if hasattr(filename_or_stream, 'read'):
        stream = filename_or_stream
    else:
        stream = open(filename_or_stream, 'rb')

    unpacker = msgpack.Unpacker(stream, encoding='utf-8')
    repacker = msgpack.Packer(encoding='utf-8')
    offset = 0
    for value in unpacker:
        if offsets:
            yield (value, offset)
            offset += len(repacker.pack(value))
        else:
            yield value


def read_msgpack_value(stream, offset):
    if offset is not None:
        stream.seek(offset)
    unpacker = msgpack.Unpacker(stream, encoding='utf-8')
    return unpacker.unpack()

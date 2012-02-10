# -*- coding: utf-8 -*-
"""
Named serializer utilities
"""

from grokcore import component as grok

from affinitic.zamqp.interfaces import ISerializer

import cPickle


class PickleSerializer(grok.GlobalUtility):
    grok.provides(ISerializer)
    grok.name("pickle")

    content_type = "application/x-python-serialize"

    def serialize(self, body):
        return cPickle.dumps(body)

    def deserialize(self, body):
        return cPickle.loads(body)


class PickleSerializerByMimeType(PickleSerializer):
    grok.provides(ISerializer)
    grok.name(PickleSerializer.content_type)


try:
    import msgpack

    class MessagePackSerializer(grok.GlobalUtility):
        grok.provides(ISerializer)
        grok.name("msgpack")

        content_type = "application/x-msgpack"

        def serialize(self, body):
            return msgpack.packb(body)

        def deserialize(self, body):
            return msgpack.unpackb(body)

    class MessagePackSerializerByMimeType(MessagePackSerializer):
        grok.provides(ISerializer)
        grok.name(MessagePackSerializer.content_type)

except ImportError:
    pass

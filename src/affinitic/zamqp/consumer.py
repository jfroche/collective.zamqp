# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import alsoProvides
from zope.component import getUtility, queryAdapter
from kombu.compat import Consumer as CarrotConsumer
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection, IMessage, IMessageWrapper
import grokcore.component as grok


class Consumer(grok.GlobalUtility, CarrotConsumer):
    __doc__ = CarrotConsumer.__doc__
    grok.baseclass()
    grok.implements(IConsumer)

    messageInterface = None
    connection_id = None

    queues = []  # kombu.messaging expects iterable here

    def __init__(self, connection=None, queue=None, exchange=None,
            routing_key=None, exchange_type=None, durable=None,
            exclusive=None, auto_delete=None, **kwargs):
        self._backend = None
        self._connection = connection
        super(Consumer, self).__init__(self.connection, queue, exchange,
                                       routing_key, exchange_type, durable,
                                       exclusive, auto_delete, **kwargs)

    @property
    def connection(self):
        if self._connection is None:
            self._connection = getUtility(IBrokerConnection, name=self.connection_id)
        return self._connection

    def getBackend(self):
        if self._backend is None:
            self._backend = self.connection.create_backend()
            if self.auto_declare:
                self.declare()
        return self._backend

    def setBackend(self, backend):
        self._backend = backend
        if self.auto_declare:
            self.declare()

    backend = property(getBackend, setBackend)

    def _adaptMessage(self, message):
        alsoProvides(message, IMessage)
        return queryAdapter(message, IMessageWrapper, default=message)

    def _markMessage(self, message):
        if self.messageInterface:
            alsoProvides(message, self.messageInterface)
        return message

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)

    receive.__doc__ = CarrotConsumer.receive.__doc__

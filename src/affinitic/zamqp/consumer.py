# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import alsoProvides
from zope.component import getUtility, queryAdapter
from carrot.messaging import Consumer as CarrotConsumer
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection, IMessage, IMessageWrapper
import grokcore.component as grok


class Consumer(grok.GlobalUtility, CarrotConsumer):
    __doc__ = CarrotConsumer.__doc__
    grok.baseclass()
    grok.implements(IConsumer)

    queue = None
    messageInterface = None
    connection_id = None

    def __init__(self, connection=None, queue=None, exchange=None,
            routing_key=None, **kwargs):
        self._connection = connection
        backend = kwargs.get("backend", None)
        if backend is not None:
            self.backend = backend
        self.queue = queue or self.queue
        self.queue = queue or self.queue
        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key
        self.callbacks = []
        self.durable = kwargs.get("durable", self.durable)
        self.exclusive = kwargs.get("exclusive", self.exclusive)
        self.auto_delete = kwargs.get("auto_delete", self.auto_delete)
        self.exchange_type = kwargs.get("exchange_type", self.exchange_type)
        self.warn_if_exists = kwargs.get("warn_if_exists",
                                         self.warn_if_exists)
        self.auto_ack = kwargs.get("auto_ack", self.auto_ack)
        self.auto_declare = kwargs.get("auto_declare", self.auto_declare)
        self._backend = None
        if self.exclusive:
            self.auto_delete = True
        self.consumer_tag = self._generate_consumer_tag()

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

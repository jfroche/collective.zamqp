# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import alsoProvides
from zope.component import getUtility
from carrot.messaging import Consumer as CarrotConsumer
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection, IMessage, IMessageWrapper
import grokcore.component as grok


class Consumer(grok.GlobalUtility, CarrotConsumer):
    grok.baseclass()
    grok.implements(IConsumer)

    queue = None

    def __init__(self):
        self._connection = None
        self._backend = None
        self.callbacks = []
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

    def as_dict(self):
        return {'exchange': self.exchange,
                'routing_key': self.routingKey}

    def receive(self, message_data, message):
        alsoProvides(message, IMessage)
        message = IMessageWrapper(message)
        alsoProvides(message, self.messageInterface)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)

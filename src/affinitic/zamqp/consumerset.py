# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import grokcore.component as grok
from zope.component import getUtilitiesFor, createObject, getUtility, queryAdapter
from zope.component.interfaces import IFactory
from zope.interface import alsoProvides, implements, implementedBy

from carrot.messaging import ConsumerSet as CarrotConsumerSet

from affinitic.zamqp.interfaces import IMessageWrapper, IConsumerSet, IConsumerSetFactory
from affinitic.zamqp.interfaces import IMessage, IConsumer


class ConsumerSet(CarrotConsumerSet):
    implements(IConsumerSet)

    def _adaptMessage(self, message):
        alsoProvides(message, IMessage)
        return queryAdapter(message, IMessageWrapper, default=message)

    def _markMessage(self, message):
        consumer = getUtility(IConsumer, message.delivery_info['exchange'])
        return consumer._markMessage(message)

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)


class ConsumerSetFactory(object):
    grok.implements(IConsumerSetFactory)

    title = 'ConsumerSet Factory'
    description = 'Help creating a new Consumer Set'

    def getInterfaces(self):
        return implementedBy(ConsumerSet)

    def __call__(self, connectionId):
        conn = createObject('AMQPBrokerConnection', connectionId)
        consumerSet = ConsumerSet(conn)
        consumerSet.connection_id = connectionId
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId:
                consumerSet.add_consumer(consumerUtility)
        return consumerSet

grok.global_utility(ConsumerSetFactory,
    provides=IFactory, name='ConsumerSet')

# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.component import getUtilitiesFor, createObject, getUtility
from zope.component.interfaces import IFactory
from zope.interface import alsoProvides
from carrot.messaging import ConsumerSet as CarrotConsumerSet
from affinitic.zamqp.interfaces import IMessageWrapper
from affinitic.zamqp.interfaces import IMessage, IConsumer
import grokcore.component as grok


class ConsumerSet(CarrotConsumerSet):

    def receive(self, message_data, message):
        alsoProvides(message, IMessage)
        message = IMessageWrapper(message)
        consumer = getUtility(IConsumer, message.delivery_info['exchange'])
        alsoProvides(message, consumer.messageInterface)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)


class ConsumerSetFactory(object):

    def __call__(self, connectionId):
        conn = createObject('AMQPBrokerConnection', connectionId)
        consumerSet = ConsumerSet(conn)
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId:
                consumerSet.add_consumer(consumerUtility)
        return consumerSet

grok.global_utility(ConsumerSetFactory,
    provides=IFactory, name='ConsumerSet')

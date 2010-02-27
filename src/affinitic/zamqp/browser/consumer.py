# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from Products.Five import BrowserView
from zope.event import notify
from zope.component import queryUtility, getUtilitiesFor
from zope.interface import alsoProvides

from carrot.messaging import ConsumerSet
from carrot.connection import BrokerConnection

from affinitic.zamqp.event import ArrivedMessage
from affinitic.zamqp.interfaces import IConsumer


class ConsumerView(BrowserView):

    def mark_message(self, message_data, message):
        channelId = message.delivery_info.get('exchange')
        interfaceClass = self.getInterfaceByChannel(channelId)
        if interfaceClass is not None:
            alsoProvides(message, interfaceClass)

    def notify_message(self, message_data, message):
        notify(ArrivedMessage(message))
        message.ack()

    def registerConsumer(self, connectionId):
        self.conn = BrokerConnection(hostname="localhost", port=5672,
                                userid="test", password="test", virtual_host="test")
        self.consumerSet = ConsumerSet(connection=self.conn)
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connectionId == connectionId:
                self.consumerSet.add_consumer_from_dict(name, **consumerUtility.as_dict())
        self.consumerSet.register_callback(self.mark_message)
        self.consumerSet.register_callback(self.notify_message)

    def getInterfaceByChannel(self, channelId):
        consumer = queryUtility(IConsumer, name=channelId)
        if consumer is not None:
            return consumer.messageInterface
        return None

    def __call__(self, message_channel):
        self.registerConsumer('test')
        list(self.consumerSet.iterconsume())

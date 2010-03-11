# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from Products.Five import BrowserView
from zope.event import notify
from zope.component import queryUtility, getUtilitiesFor, getUtility
from zope.interface import alsoProvides

from carrot.messaging import ConsumerSet

from affinitic.zamqp.event import ArrivedMessage
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection


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
        conn = getUtility(IBrokerConnection, name=connectionId)
        print conn
        self.consumerSet = ConsumerSet(connection=conn)
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId:
                self.consumerSet.add_consumer(consumerUtility)
        self.consumerSet.register_callback(self.mark_message)
        self.consumerSet.register_callback(self.notify_message)

    def getInterfaceByChannel(self, channelId):
        consumer = queryUtility(IConsumer, name=channelId)
        if consumer is not None:
            return consumer.messageInterface
        return None

    def __call__(self, message_channel):
        self.registerConsumer(message_channel)
        print 'in consumer loop'
        list(self.consumerSet.iterconsume())

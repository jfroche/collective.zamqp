# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import socket
from time import sleep
import threading
from Products.Five import BrowserView
from zope.event import notify
from zope.component import queryUtility, getUtilitiesFor, getUtility
from zope.interface import alsoProvides

from carrot.messaging import ConsumerSet

from affinitic.zamqp import logger
from affinitic.zamqp.event import ArrivedMessage
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection


class ConsumerView(BrowserView):

    def mark_message(self, message_data, message):
        channelId = message.delivery_info.get('exchange')
        interfaceClass = self.getInterfaceByChannel(channelId)
        if interfaceClass is not None:
            logger.debug('Thread %s - Mark message %s with interface %s' % (self.threadName,
                                                                            message.delivery_info.get('delivery_tag'),
                                                                            interfaceClass.__name__))
            alsoProvides(message, interfaceClass)

    def notify_message(self, message_data, message):
        logger.debug('Thread %s - Notify new message %s in exchange: %s' % (self.threadName,
                                                                            message.delivery_info.get('delivery_tag'),
                                                                            message.delivery_info.get('exchange')))
        stateBeforeNotification = message._state
        try:
            notify(ArrivedMessage(message))
            sleep(2)
        except:
            #XXX Send to Error queue ?
            pass
        else:
            logger.debug("Thread %s - Handled Message %s (status = '%s')" % (self.threadName,
                                                                             message.delivery_info.get('delivery_tag'),
                                                                             message._state))
            if message._state == stateBeforeNotification:
                #XXX nobody used the message: error queue/dead letter queue ?
                pass

    def registerConsumer(self, connectionId):
        conn = getUtility(IBrokerConnection, name=connectionId)
        self.consumerSet = ConsumerSet(connection=conn)
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId:
                self.consumerSet.add_consumer(consumerUtility)
        self.consumerSet.register_callback(self.mark_message)
        self.consumerSet.register_callback(self.notify_message)

    def clearConsumer(self, connectionId):
        conn = getUtility(IBrokerConnection, name=connectionId)
        conn._closed = None
        conn._connection = None

    def getInterfaceByChannel(self, channelId):
        consumer = queryUtility(IConsumer, name=channelId)
        if consumer is not None:
            return consumer.messageInterface
        return None

    @property
    def threadName(self):
        return threading.currentThread().getName()

    def __call__(self, message_channel):
        sleep(1)
        while(1):
            try:
                self.registerConsumer(message_channel)
                logger.info('Consuming messages in thread %s' % self.threadName)
                list(self.consumerSet.iterconsume())
            except (IOError, socket.error), err:
                logger.info('Thread %s - disconnected from message broker. Waiting ...' % self.threadName)
                self.clearConsumer(message_channel)
                sleep(10)

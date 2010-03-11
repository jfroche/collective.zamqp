# -*- coding: utf-8 -*-
"""
<+ MODULE_NAME +>

Licensed under the <+ LICENSE +> license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import random
import logging
import threading
import transaction
from time import sleep
from ZODB.POSException import ConflictError
from zope.component import queryUtility, getUtilitiesFor, getUtility
from zope.app.publication.zopepublication import ZopePublication
from zope.app.component.hooks import setSite

from carrot.messaging import ConsumerSet

from affinitic.zamqp import logger
from zope.interface import alsoProvides
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection, IArrivedMessage

log = logging.getLogger('affinitic.zamqp')

ERROR_MARKER = object()
storage = threading.local()

THREAD_STARTUP_WAIT = 0.05


class ConsumerProcessor(object):

    def __init__(self, site, waitTime=3.0):
        self.site = site
        self.sm = site.getSiteManager()

    def __call__(self, message):
        messageId = message.delivery_info.get('delivery_tag')
        exchange = message.delivery_info.get('exchange')
        logger.debug('Notify new message %s in exchange: %s' % (messageId,
                                                                exchange))
        stateBeforeNotification = message._state
        setSite(self.site)
        transaction.begin()
        try:
            self.sm.subscribers((message,), IArrivedMessage)
        except Exception, error:
            #XXX Send to Error queue ?
            log.error('Error while running job %s on exchange %s' % (messageId, exchange))
            log.exception(error)
        else:
            try:
                transaction.commit()
            except ConflictError:
                logger.error('Conflict while working on message %s' % messageId)
            else:
                ack = getattr(message, '_ack', False)
                if ack:
                    message.ack()
            logger.debug("Handled Message %s (status = '%s')" % (messageId,
                                                                 message._state))
            if message._state == stateBeforeNotification:
                #XXX nobody used the message: error queue/dead letter queue ?
                pass


class MultiProcessor(object):

    def __init__(self, db, sitePath, connectionId, waitTime=3.0):
        self.db = db
        self.connection = self.db.open()
        self.waitTime = waitTime
        self.connectionId = connectionId
        self.sitePath = sitePath
        self.registerConsumers(self.connectionId)
        self.threads = []
        self.maxThreads = 1

    @property
    def threadName(self):
        return threading.currentThread().getName()

    def getInterfaceByChannel(self, channelId):
        consumer = queryUtility(IConsumer, name=channelId)
        if consumer is not None:
            return consumer.messageInterface
        return None

    def getSite(self):
        self.root = self.connection.root()
        return getattr(self.root[ZopePublication.root_name], self.sitePath)

    def getSiteManager(self):
        return self.getSite().getSiteManager()

    def registerConsumers(self, connectionId):
        conn = getUtility(IBrokerConnection, name=connectionId).__class__()
        self.consumerSet = ConsumerSet(connection=conn)
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId:
                self.consumerSet.add_consumer(consumerUtility)
        self.consumerSet.register_callback(self.mark_message)
        self.consumerSet.register_callback(self.notify_message)

    def mark_message(self, message_data, message):
        channelId = message.delivery_info.get('exchange')
        interfaceClass = self.getInterfaceByChannel(channelId)
        if interfaceClass is not None:
            logger.debug('Thread %s - Mark message %s with interface %s' % (self.threadName,
                                                                            message.delivery_info.get('delivery_tag'),
                                                                            interfaceClass.__name__))
            alsoProvides(message, interfaceClass)

    def notify_message(self, message_data, message):
        while True:
            for thread in self.threads:
                if not thread.isAlive():
                    self.threads.remove(thread)
            if len(self.threads) == self.maxThreads:
                sleep(self.waitTime)
                continue
            else:
                sleep(random.random())
                break
        processor = ConsumerProcessor(self.getSite())
        thread = threading.Thread(
            target=processor, args=(message,))
        self.threads.append(thread)
        thread.start()

    def __call__(self):
        list(self.consumerSet.iterconsume())

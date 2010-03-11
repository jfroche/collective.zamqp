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
from zope.component import queryUtility, createObject
from zope.app.publication.zopepublication import ZopePublication
from zope.app.component.hooks import setSite

from affinitic.zamqp import logger
from affinitic.zamqp.interfaces import IConsumer, IArrivedMessage

log = logging.getLogger('affinitic.zamqp')

storage = threading.local()


class ConsumerProcessor(object):

    def __init__(self, site, waitTime=3.0):
        self.site = site
        self.sm = site.getSiteManager()

    def __call__(self, message):
        messageId = message.delivery_info.get('delivery_tag')
        exchange = message.delivery_info.get('exchange')
        logger.debug('Notify new message %s in exchange: %s' % (messageId,
                                                                exchange))
        setSite(self.site)
        #XXX all this should be implemented with a with statement
        transaction.begin()
        message._register()
        try:
            results = self.sm.subscribers((message,), IArrivedMessage)
        except Exception, error:
            #XXX Send to Error queue ?
            log.error('Error while running job %s on exchange %s' % (messageId, exchange))
            log.exception(error)
        else:
            logger.debug("Before commit Message %s (status = '%s')" % (messageId,
                                                                 message._state))
            try:
                transaction.commit()
            except ConflictError:
                logger.error('Conflict while working on message %s' % messageId)
            logger.debug("Handled Message %s (status = '%s')" % (messageId,
                                                                 message._state))
            if not results:
                #If there is no result
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
        self.consumerSet = createObject('ConsumerSet', connectionId)
        self.consumerSet.register_callback(self.notify_message)

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

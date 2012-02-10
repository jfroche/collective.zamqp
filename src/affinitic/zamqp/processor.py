# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import sys
import transaction

from ZODB.POSException import ConflictError
from zope.component import createObject, queryUtility, getUtilitiesFor

try:
    from zope.component.hooks import setSite
    setSite  # pyflakes
except ImportError:
    from zope.app.component.hooks import setSite

from affinitic.zamqp.interfaces import\
    IConsumer, IErrorConsumer, IArrivedMessage, IErrorHandler

import logging
logger = logging.getLogger('affinitic.zamqp')


class MultiProcessor(object):

    def __init__(self, db, site_id, connection_id):
        self.db = db.open()
        self.site_id = site_id

        self.connection = createObject('AMQPBrokerConnection', connection_id)

        self.consumers = []
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connection_id and \
                not IErrorConsumer.providedBy(consumerUtility):
                self.consumers.append(consumerUtility)

        self.connection.async_connect(self.on_channel_open)

    def __call__(self):
        logger.info("Starting Pika IOLoop.")
        self.connection.async_ioloop.start()
        logger.error("Pika IOLoop unexpectedly ended.")

    @property
    def site(self):
        return getattr(self.db.root()['Application'], self.site_id)

    def on_channel_open(self, channel):
        for consumer in self.consumers:
            consumer.consume(channel, self.on_message_received)

    def on_message_received(self, message):
        logger.info("Got message %s %s", message.header_frame, message.body)

    # def _adaptMessage(self, message):
    #     alsoProvides(message, IMessage)
    #     return queryAdapter(message, IMessageWrapper, default=message)

    # def _markMessage(self, message):
    #     exchange = message.delivery_info['exchange']
    #     consumer = queryUtility(IConsumer, exchange)
    #     if consumer is None:
    #         routingKey = message.delivery_info['routing_key']
    #         consumer = getUtility(IConsumer, "%s.%s" % (exchange, routingKey))
    #     return consumer._markMessage(message)

    # def receive(self, message_data, message):
    #     message = self._markMessage(message)
    #     message = self._adaptMessage(message)
    #     message = self._markMessage(message)
    #     if not self.callbacks:
    #         raise NotImplementedError("No consumer callbacks registered")
    #     for callback in self.callbacks:
    #         callback(message_data, message)


class ConsumerWorker(object):

    def __init__(self, site, waitTime=3.0):
        self.site = site
        self.sm = site.getSiteManager()

    def __call__(self, message):
        messageId = message.delivery_info.get('delivery_tag')
        exchange = message.delivery_info.get('exchange')
        logger.info('Notify new message %s in exchange: %s' % (messageId,
                                                                exchange))
        setSite(self.site)
        #XXX all this should be implemented with a with statement
        transaction.begin()
        message._register()
        try:
            results = self.sm.subscribers((message,), IArrivedMessage)
        except Exception, error:
            transaction.abort()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            errorHandler = queryUtility(IErrorHandler, name=exchange)
            if errorHandler is not None:
                errorHandler(message, error, exc_traceback)
            else:
                logger.error('Error while running job %s on exchange %s' % (messageId, exchange))
                logger.exception(error)
        else:
            logger.info("Before commit Message %s (status = '%s')" % (messageId,
                                                                 message._state))
            try:
                transaction.commit()
            except ConflictError:
                logger.error('Conflict while working on message %s' % messageId)
                transaction.abort()
            else:
                logger.info("Handled Message %s (status = '%s')" % (messageId,
                                                                     message._state))
                if not results:
                    #If there is no result
                    #XXX nobody handled the message: error queue/dead letter queue ?
                    logger.warning('Nobody handled message %s on exchange %s' % (messageId, exchange))



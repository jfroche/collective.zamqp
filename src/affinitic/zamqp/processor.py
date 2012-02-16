# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import sys
import transaction

from ZODB.POSException import ConflictError
from zope.component import\
    createObject, queryUtility, getUtilitiesFor, getSiteManager

try:
    from zope.component.hooks import setSite, setHooks
    setSite, setHooks  # pyflakes
except ImportError:
    from zope.app.component.hooks import setSite, setHooks

from affinitic.zamqp.interfaces import\
    IConsumer, IErrorConsumer, IArrivedMessage, IErrorHandler

import logging
logger = logging.getLogger('affinitic.zamqp')


class active_site:

    def __init__(self, site):
        self.site = site

    def __enter__(self):
        setSite(self.site)
        setHooks()
        return self.site

    def __exit__(self, type, value, traceback):
        setSite()
        setHooks()


class transactional_message:

    def __init__(self, message):
        self.message = message
        self.delivery_tag = message.method_frame.delivery_tag
        self.exchange = message.method_frame.exchange

    def __enter__(self):
        transaction.begin()
        self.message._register()
        return self.message

    def __exit__(self, type, value, traceback):
        if isinstance(value, Exception):
            transaction.abort()
            exc_type, exc_value, exc_traceback = sys.exc_info()

            errorHandler = queryUtility(IErrorHandler, name=self.exchange)
            if errorHandler is not None:
                errorHandler(self.message, value, exc_traceback)
            else:
                logger.error('Error while running job %s on self.exchange %s',
                             self.delivery_tag, self.exchange)
                logger.exception(value)
        else:
            logger.info('Before commit Message %s (status = %s)',
                        self.delivery_tag, self.message.state)
            try:
                transaction.commit()
            except ConflictError:
                logger.error('Conflict while working on message %s',
                             self.delivery_tag)
                transaction.abort()
            else:
                logger.info('Handled Message %s (status = %s)',
                            self.delivery_tag, self.message.state)


class MultiProcessor(object):

    def __init__(self, db, site_id, connection_id):
        self.db = db.open()
        self.site_id = site_id

        self.connection = createObject('AMQPBrokerConnection', connection_id,
                                       on_channel_open=self.on_channel_open)
        self.consumers = []
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connection_id and \
                not IErrorConsumer.providedBy(consumerUtility):
                self.consumers.append(consumerUtility)

    def __call__(self):
        logger.info('Starting Pika IOLoop.')
        self.connection.async_ioloop.start()
        # try:
        #     self.connection.async_ioloop.start()
        # except Exception as e:
        #     logger.error(e)
        logger.error('Pika IOLoop ended.')

    def on_channel_open(self, channel):
        for consumer in self.consumers:
            consumer.consume(channel, self.on_message_received)

    def on_message_received(self, message):
        message_id = message.method_frame.delivery_tag
        exchange = message.method_frame.exchange
        logger.info('Received message %s on exchange %s',
                    message_id, exchange)

        self.db.sync()  # update the view on the database
        site = getattr(self.db.root()['Application'], self.site_id)
        with active_site(site):
            sm = getSiteManager()
            try:
                with transactional_message(message):
                    results = sm.subscribers((message,), IArrivedMessage)
            except Exception as e:
                results = e
                # All exceptions are already logged by with's __exit__.
                # Also, any transactions have been aborted.

        if self.connection.tx_select and message.state == "ACK":
            try:
                message.channel.tx_commit()
            except KeyError:
                logger.warning(('Tx.Commit failed after handling of msg %s on '
                                'exchange %s. Message may be handled twice'),
                               message_id, exchange)
        elif self.connection.tx_select:
            try:
                message.channel.tx_rollback()
            except KeyError:
                pass  # Tx.Rollback is allowed to fail silently

        if not isinstance(results, Exception) and not results:
            # XXX: nobody handled the message: error queue/dead letter queue?
            logger.warning('Nobody handled message %s on exchange %s',
                           message_id, exchange)

# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import sys
import time
import random
import transaction

from ZODB.POSException import ConflictError
from zope.component import\
    createObject, queryUtility, getUtilitiesFor, getSiteManager

try:
    from zope.component.hooks import setSite, setHooks
    setSite, setHooks  # pyflakes
except ImportError:
    from zope.app.component.hooks import setSite, setHooks

from socket import error as SocketError

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
        self.exchange = message.method_frame.exchange
        self.routing_key = message.method_frame.routing_key
        self.delivery_tag = message.method_frame.delivery_tag

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
                logger.error(('Error while handling message %s sent to %s '
                              'with routing key %s'),
                             self.delivery_tag, self.exchange,
                             self.routing_key)
                logger.exception(value)
        else:
            logger.info('Committing transaction for message %s (status = %s)',
                        self.delivery_tag, self.message.state)
            try:
                transaction.commit()
                logger.info('Handled message %s (status = %s)',
                            self.delivery_tag, self.message.state)
            except ConflictError:
                transaction.abort()
                logger.error(('Conflict while working on message %s '
                              '(status = %s)'),
                             self.delivery_tag, self.message.state)
                raise  # raise to require handling also above 'with'


class MultiProcessor(object):

    def __init__(self, db, site_id, connection_id):
        self.db = db.open()
        self.site_id = site_id
        self.connection_id = connection_id

        self.connection = None
        self.consumers = []

    def __call__(self):
        # 1) create connection
        reconnection_delay = 1.0
        while True:
            try:
                self.connection = createObject(
                    'AMQPBrokerConnection', self.connection_id,
                    on_channel_open=self.on_channel_open)
            except SocketError as e:
                logger.error(e)
            finally:
                if not self.connection:
                    logger.info("Trying reconnection in %s seconds",
                                reconnection_delay)
                    time.sleep(reconnection_delay)
                    if reconnection_delay <= 60:
                        reconnection_delay *= (random.random() * 0.5) + 1
                else:
                    break

        # 2) register consumers
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == self.connection_id and \
                not IErrorConsumer.providedBy(consumerUtility):
                self.consumers.append(consumerUtility)

        # 3) start Pika IOLoop
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
        exchange = message.method_frame.exchange
        routing_key = message.method_frame.routing_key
        delivery_tag = message.method_frame.delivery_tag
        logger.info(('Received message %s sent to exchange %s with routing '
                     'key %s'),
                    delivery_tag, exchange, routing_key)

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

        # On transactional channel, commit if message has been acked
        if self.connection.tx_select and message.state == 'ACK':
            try:
                message.channel.tx_commit()
            except KeyError:
                logger.warning(('Tx.Commit failed after handling of message '
                                '%s. Message may be handled twice.'),
                               delivery_tag)

        # On transactional channel, rollback if message has not been acked
        elif self.connection.tx_select:
            try:
                message.channel.tx_rollback()
            except KeyError:
                pass  # XXX: Tx.Rollback is allowed to fail silently

        # 'Re-schedule' failed messages to be tried again later on
        if isinstance(results, Exception) and message.state != 'ACK':
            logger.warning(('Failed to handle message %s sent to exchange %s '
                            'with routing key %s; TODO: schedule re-run!'),
                           delivery_tag, exchange, routing_key)

        # Log unhandled messages; they are not acked and will be read againg
        elif not isinstance(results, Exception) and message.state != 'ACK':
            # XXX: nobody handled the message: error queue/dead letter queue?
            logger.warning(('Nobody handled message %s sent to exchange %s '
                            'with routing key %s'),
                           delivery_tag, exchange, routing_key)

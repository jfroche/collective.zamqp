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
import threading
import transaction

from App.config import getConfiguration

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


class ConsumingService(object):

    def __init__(self, db, site_id, connection_id):

        self.db = db.open()
        self.site_id = site_id
        self.connection_id = connection_id

        self.consumers = []
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == self.connection_id and \
                not IErrorConsumer.providedBy(consumerUtility):
                self.consumers.append(consumerUtility)

        self.connection = None
        self.reconnection_delay = 1.0

    def __call__(self):
        while True:
            logger.info('Creating a new Pika connection')
            try:
                self.connection = createObject(
                    'AMQPBrokerConnection', self.connection_id,
                    on_channel_open=self.on_channel_open)
                self.connection.async_ioloop.start()
            except SocketError as e:
                logger.error('Connection failed or closed unexpectedly: %s', e)
            except TypeError as e:
                logger.error('Connection failed or closed unexpectedly: %s', e)
            finally:
                if self.reconnection_delay <= 60:
                    self.reconnection_delay *= (random.random() * 0.5) + 1
                logger.info("Trying reconnection in %s seconds",
                            self.reconnection_delay)
                time.sleep(self.reconnection_delay)

    def on_channel_open(self, channel):
        self.reconnection_delay = 1.0
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


def launch(event):
    """Start the queue processing services based on the settings in
    zope.conf on 'IDatabaseOpenedWithRoot' event"""

    # Read product configuration
    config = getattr(getConfiguration(), 'product_config', {})
    product_config = config.get('affinitic.zamqp', {})

    # Start configured services
    for service_id, opts in product_config.items():
        site_id, connection_id = opts.split('@')
        connection_id = connection_id.split(' ')[0]  # clean deprecated opts.

        # Start the thread running the processor inside
        processor = ConsumingService(event.database, site_id, connection_id)

        thread = threading.Thread(target=processor, name=service_id)
        thread.setDaemon(True)
        thread.running = True
        thread.start()

        logger.info('Starting AMQP-processor %s', service_id)

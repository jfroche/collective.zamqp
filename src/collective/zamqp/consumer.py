# -*- coding: utf-8 -*-
###
# collective.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright by Affinitic sprl
# Copyright (c) 2012 University of Jyväskylä
###
"""Consumer utility base class"""

import sys

import grokcore.component as grok

from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import getSecurityManager

from ZODB.POSException import ConflictError

from zope.interface import alsoProvides
from zope.component import createObject, queryUtility
from zope.component.hooks import getSite
from zope.event import notify

from Products.Five.browser import BrowserView

from collective.zamqp.interfaces import IConsumer, IErrorHandler

import logging
logger = logging.getLogger('collective.zamqp')


class Consumer(grok.GlobalUtility):
    """Consumer utility base class"""

    grok.baseclass()
    grok.implements(IConsumer)

    connection_id = None

    exchange = None
    routing_key = None
    durable = True

    exchange_type = 'direct'
    exchange_durable = None

    queue = None
    queue_durable = None
    queue_exclusive = False
    queue_arguments = {}

    auto_declare = True

    auto_ack = False
    marker = None

    def __init__(self, connection_id=None, exchange=None, routing_key=None,
                 durable=None, exchange_type=None, exchange_durable=None,
                 queue=None, queue_durable=None, queue_exclusive = None,
                 queue_arguments=None, auto_declare=None, auto_ack=None,
                 marker=None):

        # Allow class variables to provide defaults
        self.connection_id = connection_id or self.connection_id

        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key
        if durable is not None:
            self.durable = durable

        self.exchange_type = exchange_type or self.exchange_type
        if exchange_durable is not None:
            self.exchange_durable = exchange_durable
        elif self.exchange_durable is None:
            self.exchange_durable = self.durable

        self.queue = queue or self.queue
        if not self.routing_key:
            self.routing_key = self.queue
        if queue_durable is not None:
            self.queue_durable = queue_durable
        elif self.queue_durable is None:
            self.queue_durable = self.durable
        if queue_exclusive is not None:
            self.queue_exclusive = queue_exclusive
        if queue_arguments is not None:
            self.queue_arguments = queue_arguments

        if auto_declare is not None:
            self.auto_declare = auto_declare

        if auto_ack is not None:
            self.auto_ack = auto_ack

        self.marker = marker or self.marker

        # BBB for affinitic.zamqp
        if getattr(self, "messageInterface", None):
            from zope.deprecation import deprecated
            self.marker = self.messageInterface
            self.messageInterface =\
                deprecated(self.messageInterface,
                           ('Consumer.messageInterface is no more. '
                            'Please, use Consumer.marker instead.'))

    def consume(self, channel, tx_select, on_message_received):
        self._channel = channel
        self._tx_select = tx_select
        self._message_received_callback = on_message_received

        if self.auto_declare and self.exchange:
            self.declare_exchange()
        elif self.auto_declare and self.queue:
            self.declare_queue()
        else:
            self.on_ready_to_consume()

    def declare_exchange(self):
        self._channel.exchange_declare(exchange=self.exchange,
                                       type=self.exchange_type,
                                       durable=self.exchange_durable,
                                       auto_delete=not self.exchange_durable,
                                       callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        logger.info("Consumer declared exchange '%s'", self.exchange)
        if self.auto_declare and self.queue:
            self.declare_queue()
        else:
            self.on_ready_to_consume()

    def declare_queue(self):
        self._channel.queue_declare(queue=self.queue,
                                    durable=self.queue_durable,
                                    exclusive=self.queue_exclusive,
                                    auto_delete=not self.queue_durable,
                                    arguments=self.queue_arguments,
                                    callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        logger.info("Consumer declared queue '%s'", self.queue)
        if self.auto_declare and self.exchange:
            self.bind_queue()
        else:
            self.on_ready_to_consume()

    def bind_queue(self):
        self._channel.queue_bind(exchange=self.exchange, queue=self.queue,
                                 routing_key=self.routing_key,
                                 callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        logger.info("Consumer bound queue '%s' to exchange '%s'",
                    self.queue, self.exchange)
        self.on_ready_to_consume()

    def on_ready_to_consume(self):
        queue = self.queue\
            or getattr(self, 'grokcore.component.directive.name', None)
        logger.info("Consumer ready to consume queue '%s'", queue)
        self._channel.basic_consume(self.on_message_received, queue=queue)

    def on_message_received(self, channel, method_frame, header_frame, body):
        message = createObject('AMQPMessage',
                               body=body,
                               header_frame=header_frame,
                               method_frame=method_frame,
                               channel=self._channel,
                               tx_select=self._tx_select)
        if self.marker:
            alsoProvides(message, self.marker)

        if self.auto_ack:
            message.ack()  # immediate ack here (doesn't wait for transaction)

        self._message_received_callback(message)


class security_manager:

    def __init__(self, request, user_id):
        self.request = request

        site = getSite()
        acl_users = site.get('acl_users')
        if acl_users:
            user = acl_users.getUser(user_id)

        if not user:
            root = site.getPhysicalRoot()
            acl_users = root.get('acl_users')
            if acl_users:
                user = acl_users.getUser(user_id)
        if user:
            user = user.__of__(acl_users)

        self.user = user

    def __enter__(self):
        self.old_security_manager = getSecurityManager()
        if self.user:
            return newSecurityManager(self.request, self.user)
        else:
            return self.old_security_manager

    def __exit__(self, type, value, traceback):
        if self.user:
            setSecurityManager(self.old_security_manager)


class ConsumingView(BrowserView):

    def __call__(self):
        message = self.request.environ.get('AMQP_MESSAGE')
        user_id = self.request.environ.get('AMQP_USER_ID')

        exchange = message.method_frame.exchange
        routing_key = message.method_frame.routing_key
        delivery_tag = message.method_frame.delivery_tag

        message._register()
        event = createObject('AMQPMessageArrivedEvent', message)
        with security_manager(self.request, user_id):
            try:
                notify(event)
            except ConflictError:
                logger.error(("Conflict while working on message '%s' "
                              "(status = '%s')"),
                             self.delivery_tag, self.message.state)
                raise
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_handler = queryUtility(IErrorHandler, name=exchange)
                if err_handler is not None:
                    err_handler(message, exc_value, exc_traceback)
                else:
                    logger.error(("Error while handling message '%s' sent to "
                                  "exchange '%s' with routing key '%s'"),
                                 delivery_tag, exchange, routing_key)
                    raise

        if not message.acknowledged:
            logger.warning(("Nobody acknowledged message '%s' sent to exchange "
                            "exchange '%s' with routing key '%s'"),
                           delivery_tag, exchange, routing_key)
        else:
            logger.info(("Letting Zope to commit database transaction for "
                         u"message '%s' (status = '%s')"),
                        delivery_tag, message.state)

# -*- coding: utf-8 -*-
###
# affinitic.zamqp
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

from affinitic.zamqp.interfaces import IConsumer, IErrorHandler

import logging
logger = logging.getLogger('affinitic.zamqp')


class Consumer(grok.GlobalUtility):
    """Consumer utility base class"""

    grok.baseclass()
    grok.implements(IConsumer)

    connection_id = None

    queue = None
    routing_key = None
    durable = True
    exclusive = False
    auto_delete = False
    arguments = {}

    exchange = None
    exchange_type = 'direct'
    exchange_durable = None
    exchange_auto_delete = None
    exchange_auto_declare = None

    auto_declare = True
    auto_ack = False
    marker = None

###
    queue = None

    queue_durable = True
    queue_exclusive = False
    queue_auto_delete = False
    queue_arguments = {}

    exchange = None

    exchange_type = 'direct'
    exchange_durable = None
    exchange_auto_delete = None

    routing_key = None

    auto_declare = True

    def __init__(self, connection_id=None,
                 queue=None, routing_key=None, durable=None,
                 exclusive=None, auto_delete=None, arguments=None,
                 exchange=None, exchange_type=None, exchange_durable=None,
                 exchange_auto_delete=None, exchange_auto_declare=None,
                 auto_declare=None, auto_ack=None, marker=None):

        # Allow class variables to provide defaults
        self.connection_id = connection_id or self.connection_id

        self.queue = queue or self.queue\
            or getattr(self, 'grokcore.component.directive.name', None)
        self.routing_key = routing_key or self.routing_key or self.queue

        if durable is not None:
            self.durable = durable
        if exclusive is not None:
            self.exclusive = exclusive
        if auto_delete is not None:
            self.auto_delete = auto_delete
        if arguments is not None:
            self.arguments = arguments

        self.exchange = exchange or self.exchange
        self.exchange_type = exchange_type or self.exchange_type

        if exchange_durable is not None:
            self.exchange_durable = exchange_durable
        elif self.exchange_durable is None:
            self.exchange_durable = self.durable
        if exchange_auto_delete is not None:
            self.exchange_auto_delete = exchange_auto_delete
        elif self.exchange_auto_delete is None:
            self.exchange_auto_delete = self.auto_delete

        if auto_declare is not None:
            self.auto_declare = auto_declare
        elif not self.exchange:
            self.auto_declare = False
        if exchange_auto_declare is not None:
            self.exchange_auto_declare = exchange_auto_declare
        elif self.exchange_auto_declare is None:
            self.exchange_auto_declare = self.auto_declare

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

        if self.exchange_auto_declare:
            self.declare_exchange()
        elif self.auto_declare:
            self.declare_queue()
        else:
            self.on_ready_to_consume()

    def declare_exchange(self):
        self._channel.exchange_declare(exchange=self.exchange,
                                       type=self.exchange_type,
                                       durable=self.exchange_durable,
                                       auto_delete=self.exchange_auto_delete,
                                       callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        logger.info("Consumer declared exchange '%s'", self.exchange)
        if self.auto_declare:
            self.declare_queue()
        else:
            self.on_ready_to_consume()

    def declare_queue(self):
        self._channel.queue_declare(queue=self.queue, durable=self.durable,
                                    exclusive=self.exclusive,
                                    auto_delete=self.auto_delete,
                                    arguments=self.arguments,
                                    callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        logger.info("Consumer declared queue '%s'", self.queue)
        self.bind_queue()

    def bind_queue(self):
        self._channel.queue_bind(exchange=self.exchange, queue=self.queue,
                                 routing_key=self.routing_key,
                                 callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        logger.info("Consumer bound queue '%s' to exchange '%s'",
                    self.queue, self.exchange)
        self.on_ready_to_consume()

    def on_ready_to_consume(self):
        logger.info("Consumer ready to consume queue '%s'", self.queue)
        self._channel.basic_consume(self.on_message_received, queue=self.queue)

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
        message = self.request.message
        exchange = self.request.message.method_frame.exchange
        routing_key = message.method_frame.routing_key
        delivery_tag = message.method_frame.delivery_tag

        message._register()
        event = createObject('AMQPMessageArrivedEvent', message)
        with security_manager(self.request, self.request.user_id):
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
            logger.warning(("Nobody acknowledgd message '%s' sent to exchange "
                            "exchange '%s' with routing key '%s'"),
                           delivery_tag, exchange, routing_key)
        else:
            logger.info(("Letting Zope to commit database transaction for "
                         u"message '%s' (status = '%s')"),
                        delivery_tag, message.state)

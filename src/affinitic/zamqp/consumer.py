# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import sys

import grokcore.component as grok

from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import getSecurityManager

from ZODB.POSException import ConflictError

from zope.interface import alsoProvides
from zope.component import createObject, queryUtility
from zope.event import notify

from Products.CMFCore.utils import getToolByName

from affinitic.zamqp.interfaces import\
    IConsumer, IMessageArrivedEvent, IErrorHandler

from Products.Five.browser import BrowserView

import logging
logger = logging.getLogger('affinitic.zamqp')


class Consumer(grok.GlobalUtility):
    """
    Consumer utility base class

    See `<#affinitic.zamqp.interfaces.IConsumer>`_ for more details.
    """
    grok.baseclass()
    grok.implements(IConsumer)

    connection_id = None

    exchange = None
    exchange_type = "direct"
    exchange_durable = None
    exchange_auto_delete = None

    queue = None
    routing_key = None
    durable = True
    exclusive = False
    auto_delete = False
    auto_declare = True
    arguments = {}

    marker = None

    def __init__(self, connection_id=None,
                 queue=None, exchange=None, exchange_type=None,
                 routing_key=None, durable=None, exclusive=None,
                 auto_delete=None, auto_declare=None, arguments=None,
                 exchange_durable=None, exchange_auto_delete=None):

        # Allow class variables to provide defaults
        self.connection_id = connection_id or self.connection_id
        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key
        self.exchange_type = exchange_type or self.exchange_type

        if durable is not None:
            self.durable = durable

        if exclusive is not None:
            self.exclusive = exclusive

        if auto_declare is not None:
            self.auto_declare = auto_declare

        if auto_delete is not None:
            self.auto_delete = auto_delete

        if arguments is not None:
            self.arguments = arguments

        if exchange_durable is not None:
            self.exchange_durable = exchange_durable
        elif self.exchange_durable is None:
            self.exchange_durable = self.durable

        if exchange_auto_delete is not None:
            self.exchange_auto_delete = exchange_auto_delete
        elif self.exchange_auto_delete is None:
            self.exchange_auto_delete = self.auto_delete

    def consume(self, channel, tx_select, on_message_received):
        self._message_received_callback = on_message_received
        self._tx_select = tx_select

        self.channel = channel
        if self.auto_declare:
            self.declare()
        else:
            self.on_ready_to_consume()

    def declare(self):
        # Next: declare exchange
        self.channel.exchange_declare(exchange=self.exchange,
                                      type=self.exchange_type,
                                      durable=self.exchange_durable,
                                      auto_delete=self.exchange_auto_delete,
                                      callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        logger.info("Declared exchange '%s'", self.exchange)
        # Next: declare queue
        self.channel.queue_declare(queue=self.queue, durable=self.durable,
                                   exclusive=self.exclusive,
                                   auto_delete=self.auto_delete,
                                   arguments=self.arguments,
                                   callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        logger.info("Declared queue '%s'", self.queue)
        # Next: bind queue
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue,
                                routing_key=self.routing_key or self.queue,
                                callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        logger.info("Bound queue '%s' to exchange '%s'",
                    self.queue, self.exchange)
        self.on_ready_to_consume()

    def on_ready_to_consume(self):
        self.channel.basic_consume(self.on_message_received, queue=self.queue)

    def on_message_received(self, channel, method_frame, header_frame, body):
        message = createObject('AMQPMessage',
                               body=body,
                               header_frame=header_frame,
                               method_frame=method_frame,
                               channel=channel,
                               tx_select=self._tx_select)
        if self.marker:
            alsoProvides(message, self.marker)
        self._message_received_callback(message)


class security_manager:

    def __init__(self, request, user):
        self.request = request
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

        mtool = getToolByName(self.context, "portal_membership")
        member = mtool.getMemberById(self.request.user_id)
        if member:
            acl_users = self.context.getPhysicalRoot().restrictedTraverse(
                getToolByName(self.context, "acl_users").getPhysicalPath())
            user = member.getUser().__of__(acl_users)
        else:
            user = None

        message._register()
        event = createObject('AMQPMessageArrivedEvent', message)
        with security_manager(self.request, user):
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
            logger.info(("Committing transaction for message '%s' "
                         u"(status = '%s')"),
                        delivery_tag, message.state)

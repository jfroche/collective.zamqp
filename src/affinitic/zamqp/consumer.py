# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import grokcore.component as grok

from zope.interface import alsoProvides
from zope.component import getUtility, queryUtility, queryAdapter

from affinitic.zamqp.interfaces import\
    IConsumer, IBrokerConnection, IMessage, IMessageWrapper


class Consumer(grok.GlobalUtility):
    """
    Consumer utility base class

    See `<#affinitic.zamqp.interfaces.IConsumer>`_ for more details.
    """
    grok.baseclass()
    grok.implements(IConsumer)

    connection_id = None

    queue = None
    exchange = None
    exchange_type = None
    routing_key = None

    durable = True
    exclusive = True
    auto_delete = True

    auto_declare = True
    queue_arguments = {}

    messageInterface = None

    def __init__(self, queue=None, exchange=None, exchange_type=None,
                 routing_key=None, durable=None, exclusive=None,
                 auto_delete=None, auto_declare=None, queue_arguments=None):

        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key
        self.exchange_type = exchange_type or self.exchange_type

        if durable is not None:
            self.durable = durable

        if exclusive is not None:
            self.exclusive = exclusive

        if auto_delete is not None:
            self.auto_delete = auto_delete

        if queue_arguments is not None:
            self.queue_arguments = queue_arguments

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
        import pdb; pdb.set_trace()
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)

    def _adaptMessage(self, message):
        alsoProvides(message, IMessage)
        return queryAdapter(message, IMessageWrapper, default=message)

    def _markMessage(self, message):
        if self.messageInterface:
            alsoProvides(message, self.messageInterface)
        return message

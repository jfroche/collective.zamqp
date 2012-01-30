# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from zope.interface import alsoProvides
from zope.component import getUtility, queryUtility, queryAdapter
from kombu.compat import Consumer as CarrotConsumer
from affinitic.zamqp.interfaces import IConsumer, IBrokerConnection, IMessage, IMessageWrapper
import grokcore.component as grok


class Consumer(grok.GlobalUtility, CarrotConsumer):
    __doc__ = CarrotConsumer.__doc__
    grok.baseclass()
    grok.implements(IConsumer)

    messageInterface = None
    connection_id = None

    def __init__(self, connection=None, queue=None, exchange=None,
            routing_key=None, exchange_type=None, durable=None,
            exclusive=None, auto_delete=None, **kwargs):

        if connection:
            self._connection = connection
        else:
            self._connection =\
                queryUtility(IBrokerConnection, name=self.connection_id)

        # Allow class variables to provide defaults
        queue = queue or getattr(self, "queue", None)
        exchange = exchange or getattr(self, "exchange", None)
        routing_key = routing_key or getattr(self, "routing_key", None)
        exchange_type = exchange_type or getattr(self, "exchange_type", None)
        durable = durable or getattr(self, "durable", None)
        exclusive = exclusive or getattr(self, "exclusive", None)
        auto_delete = auto_delete or getattr(self, "auto_delete", None)

        no_ack = not kwargs.get("auto_ack", getattr(self, "auto_ack", True))
        auto_declare = kwargs.get("auto_declare",
                                  getattr(self, "auto_declare", None))

        kwargs.update({
            "no_ack": no_ack,
            "auto_declare": auto_declare
            })

        if self._connection:
            super(Consumer, self).__init__(
                self._connection, queue, exchange, routing_key, exchange_type,
                durable, exclusive, auto_delete, **kwargs)
        else:
            kwargs.update({
                "queue": queue, "exchange": exchange,
                "routing_key": routing_key, "exchange_type": exchange_type,
                "durable": durable, "exclusive": exclusive,
                "auto_delete": auto_delete
                })
            self._lazy_init_kwargs = kwargs

    @property
    def connection(self):
        if self._connection is None:
            # perform lazy init when connection is needed for the first time
            self._connection =\
                getUtility(IBrokerConnection, name=self.connection_id)
            super(Consumer, self).__init__(
                self._connection, **self._lazy_init_kwargs)
        return self._connection

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)
    receive.__doc__ = CarrotConsumer.receive.__doc__

    def _adaptMessage(self, message):
        alsoProvides(message, IMessage)
        return queryAdapter(message, IMessageWrapper, default=message)

    def _markMessage(self, message):
        if self.messageInterface:
            alsoProvides(message, self.messageInterface)
        return message

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
    Consumer utility

    See `<#affinitic.zamqp.interfaces.IConsumer>`_ for more details.
    """
    grok.baseclass()
    grok.implements(IConsumer)

    connection_id = None

    queue = None
    exchange = None
    exchange_type = None
    routing_key = None

    auto_delete = None

    messageInterface = None

    # @property
    # def connection(self):
    #     if self._connection is None:
    #         # perform lazy init when connection is needed for the first time
    #         self._connection =\
    #             getUtility(IBrokerConnection, name=self.connection_id)
    #         super(Consumer, self).__init__(
    #             self._connection, **self._lazy_init_kwargs)
    #     return self._connection

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
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

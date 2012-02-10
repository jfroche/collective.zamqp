# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import grokcore.component as grok

from zope.component import\
    getUtilitiesFor, createObject, getUtility, queryAdapter, queryUtility
from zope.component.interfaces import IFactory
from zope.interface import alsoProvides, implements, implementedBy

from affinitic.zamqp.interfaces import\
    IMessage, IConsumer, IErrorConsumer,\
    IMessageWrapper, IConsumerSet, IConsumerSetFactory


class ConsumerSet(object):
    implements(IConsumerSet)

    def __init__(self, connection_id):
        self.connection = createObject('AMQPBrokerConnection', connection_id)
        self.consumers = []
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connection_id and \
                not IErrorConsumer.providedBy(consumerUtility):
                self.consumers.append(consumerUtility)
        self.connection.connect(self.on_connect)

    def on_connect(self, connection):
        import pdb; pdb.set_trace()

    def register_callback(self, callback):
        import pdb; pdb.set_trace()

    def _adaptMessage(self, message):
        alsoProvides(message, IMessage)
        return queryAdapter(message, IMessageWrapper, default=message)

    def _markMessage(self, message):
        exchange = message.delivery_info['exchange']
        consumer = queryUtility(IConsumer, exchange)
        if consumer is None:
            routingKey = message.delivery_info['routing_key']
            consumer = getUtility(IConsumer, "%s.%s" % (exchange, routingKey))
        return consumer._markMessage(message)

    def receive(self, message_data, message):
        message = self._markMessage(message)
        message = self._adaptMessage(message)
        message = self._markMessage(message)
        if not self.callbacks:
            raise NotImplementedError("No consumer callbacks registered")
        for callback in self.callbacks:
            callback(message_data, message)


class ConsumerSetFactory(object):
    grok.implements(IConsumerSetFactory)

    title = u'ConsumerSet Factory'
    description = u'Help creating a new Consumer Set'

    def getInterfaces(self):
        return implementedBy(ConsumerSet)

    def __call__(self, connection_id):
        return ConsumerSet(connection_id)

grok.global_utility(ConsumerSetFactory,
                    provides=IFactory, name='ConsumerSet')

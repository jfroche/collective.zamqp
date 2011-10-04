# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from zope.component import createObject
from zope.component import subscribers
from zope.component import getUtilitiesFor
from zope.component import IFactory
import grokcore.component as grok
from affinitic.zamqp.consumerset import ConsumerSetFactory, ConsumerSet
from affinitic.zamqp.interfaces import IErrorFixerHandler
from affinitic.zamqp.interfaces import IConsumer, IErrorConsumer


class ErrorManager(object):

    def __init__(self, connectionId):
        self.connectionId = connectionId

    @property
    def errors(self):
        consumers = createObject('ErrorConsumerSet', self.connectionId)
        consumers.register_callback(self.handleErrorMessage)
        return consumers.iterconsume()

    def handleErrorMessage(self, data, message):
        for errorFixerHandler in subscribers((data, message), IErrorFixerHandler):
            if errorFixerHandler.match():
                errorFixerHandler.fix()

    def main(self):
        list(self.errors)


class ErrorConsumerSetFactory(ConsumerSetFactory):

    def __call__(self, connectionId):
        conn = createObject('AMQPBrokerConnection', connectionId)
        consumerSet = ConsumerSet(conn)
        consumerSet.connection_id = connectionId
        for name, consumerUtility in getUtilitiesFor(IConsumer):
            if consumerUtility.connection_id == connectionId and \
                IErrorConsumer.providedBy(consumerUtility):
                consumerSet.add_consumer(consumerUtility)
        return consumerSet

grok.global_utility(ErrorConsumerSetFactory,
    provides=IFactory, name='ErrorConsumerSet')

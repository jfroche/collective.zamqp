# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.component import getUtility
from zope.component.interfaces import IFactory
import grokcore.component as grok
from carrot.connection import BrokerConnection as CarrotBrokerConnection
from affinitic.zamqp.interfaces import IBrokerConnection


class BrokerConnection(grok.GlobalUtility, CarrotBrokerConnection):
    grok.implements(IBrokerConnection)
    grok.baseclass()

    def __init__(self):
        self._closed = None
        self._connection = None


class BrokerConnectionFactory(object):
    grok.implements(IFactory)

    def __call__(self, connectionId):
        return getUtility(IBrokerConnection, name=connectionId).__class__()


grok.global_utility(BrokerConnectionFactory,
    provides=IFactory, name='AMQPBrokerConnection')

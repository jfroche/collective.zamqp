# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import implementedBy
import grokcore.component as grok
from carrot.connection import BrokerConnection as CarrotBrokerConnection
from affinitic.zamqp.interfaces import IBrokerConnection, IBrokerConnectionFactory


class BrokerConnection(grok.GlobalUtility, CarrotBrokerConnection):
    """
    Connection utility to the message broker

    See `<#affinitic.zamqp.interfaces.IBrokerConnection>`_ for more details.
    """
    grok.implements(IBrokerConnection)
    grok.baseclass()

    port = 5672
    password = None
    userid = None
    hostname = None
    virtualHost = None
    id = None

    def __init__(self):
        self._closed = None
        self._connection = None


class BrokerConnectionFactory(object):
    grok.implements(IBrokerConnectionFactory)

    title = 'BrokerConnection Factory'
    description = 'Help creating a new Broker connection'

    def getInterfaces(self):
        return implementedBy(BrokerConnection)

    def __call__(self, connectionId):
        return getUtility(IBrokerConnection, name=connectionId).__class__()


grok.global_utility(BrokerConnectionFactory,
    provides=IFactory, name='AMQPBrokerConnection')

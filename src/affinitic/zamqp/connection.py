# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import grokcore.component as grok
from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import implementedBy

from kombu.connection import BrokerConnection as KombuBrokerConnection

from affinitic.zamqp.interfaces import IBrokerConnection, IBrokerConnectionFactory


class BrokerConnection(grok.GlobalUtility, KombuBrokerConnection):
    """
    Connection utility to the message broker

    See `<#affinitic.zamqp.interfaces.IBrokerConnection>`_ for more details.
    """
    grok.implements(IBrokerConnection)
    grok.baseclass()

    id = None  # only one not already defined in KombuBrokerConnection
    hostname = None
    port = 5672  # is defined None in KombuBrokerConnection
    userid = None
    password = None
    virtual_host = "/"


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

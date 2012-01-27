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

    id = None
    hostname = "localhost"
    port = 5672
    userid = None
    password = None
    virtual_host = "/"

    def __init__(self, hostname=None, userid=None,
                 password=None, virtual_host=None, port=None, insist=False,
                 ssl=False, transport=None, connect_timeout=5,
                 transport_options=None, login_method=None, **kwargs):

        # Allow class variables to provide defaults
        hostname = hostname or self.hostname
        port = port or self.port
        userid = userid or self.userid
        password = password or self.password
        virtual_host = virtual_host or self.virtual_host

        super(BrokerConnection, self).__init__(
            hostname, userid, password, virtual_host, port, insist,
            ssl, transport, login_method, **kwargs)


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

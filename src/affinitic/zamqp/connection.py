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

from pika import\
    PlainCredentials, ConnectionParameters, SelectConnection,\
    BasicProperties
from pika.reconnection_strategies import SimpleReconnectionStrategy

from affinitic.zamqp.interfaces import\
    IBrokerConnection, IBrokerConnectionFactory

import logging
logger = logging.getLogger('affinitic.zamqp')


class BrokerConnection(grok.GlobalUtility):
    """
    Connection utility to the message broker

    See `<#affinitic.zamqp.interfaces.IBrokerConnection>`_ for more details.
    """
    grok.implements(IBrokerConnection)
    grok.baseclass()

    hostname = "localhost"
    port = 5672
    virtual_host = "/"

    userid = None
    password = None

    def __init__(self):
        self.connecting = False
        self.connected = False

    def connect(self):
        if self.connecting or self.connected:
            return

        # https://github.com/pika/pika/blob/master/pika/connection.py
        self.connecting = True

        credentials = PlainCredentials(self.userid, self.password,
                                       erase_on_connect=False)
        parameters = ConnectionParameters(self.hostname, self.port,
                                          self.virtual_host,
                                          credentials=credentials)
        strategy = SimpleReconnectionStrategy()

        self.connection = SelectConnection(parameters=parameters,
                                           on_open_callback=self.on_connect,
                                           reconnection_strategy=strategy)

    def on_connect(self, connection):
        self.connecting = False
        self.connected = True
        logger.info("Connected")
        import pdb; pdb.set_trace()


class BrokerConnectionFactory(object):
    grok.implements(IBrokerConnectionFactory)

    title = u'BrokerConnection Factory'
    description = u'Help creating a new Broker connection'

    def getInterfaces(self):
        return implementedBy(BrokerConnection)

    def __call__(self, connection_id):
        return getUtility(IBrokerConnection, name=connection_id).__class__()

grok.global_utility(BrokerConnectionFactory,
                    provides=IFactory, name='AMQPBrokerConnection')

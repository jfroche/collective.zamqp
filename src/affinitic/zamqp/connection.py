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
    PlainCredentials, ConnectionParameters,\
    SelectConnection, BlockingConnection
from pika.reconnection_strategies import SimpleReconnectionStrategy

from affinitic.zamqp.interfaces import\
    IBrokerConnection, IBrokerConnectionFactory

import logging
logger = logging.getLogger('affinitic.zamqp')


class BrokerConnection(grok.GlobalUtility):
    """
    Connection utility base class

    See `<#affinitic.zamqp.interfaces.IBrokerConnection>`_ for more details.
    """
    grok.implements(IBrokerConnection)
    grok.baseclass()

    hostname = "localhost"
    port = 5672
    virtual_host = "/"

    userid = None
    password = None

    tx_select = None

    def __init__(self, hostname=None, port=None, virtual_host=None,
                 userid=None, password=None, tx_select=None):

        self._sync_connection = None
        self._sync_channel = None

        self._async_connection = None
        self._async_connecting = False

        # Allow class variables to provide defaults
        self.hostname = hostname or self.hostname
        self.port = port or self.port
        self.virtual_host = virtual_host or self.virtual_host

        self.userid = userid or self.userid
        self.password = password or self.password

        if tx_select is not None:
            self.tx_select = tx_select

    @property
    def connection(self):
        if not self._sync_connection:
            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials)
            strategy = SimpleReconnectionStrategy()
            self._sync_connection = BlockingConnection(
                parameters=parameters, reconnection_strategy=strategy)
        return self._sync_connection

    @property
    def channel(self):
        if not self._sync_channel:
            self._sync_channel = self.connection.channel()
            if self.tx_select:  # should channel be transactional
                self._sync_channel.tx_select()
        return self._sync_channel

    def async_connect(self):
        if not self._async_connection or not self._async_connecting:
            self._async_connecting = True
            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials)
            strategy = SimpleReconnectionStrategy()
            self._async_connection = SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_async_connect,
                reconnection_strategy=strategy)

    def on_async_connect(self, connection):
        self._async_connection = connection
        self._async_connecting = False
        import pdb; pdb.set_trace()

    # def declare(self):
    #     if self.auto_declare:
    #         self.connection.channel.exchange_declare(
    #             exchange=self.exchange, type=self.exchange_type,
    #             durable=self.durable, auto_delete=self.auto_delete)
    #         self.connection.channel.queue_declare(
    #             queue=self.queue, durable=self.durable,
    #             exclusive=self.exclusive, auto_delete=self.auto_delete,
    #             arguments=self.queue_arguments)
    #         self.connection.channel.queue_bind(
    #             exchange=self.exchange, queue=self.queue,
    #             routing_key=self.routing_key or '')


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

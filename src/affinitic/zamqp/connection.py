# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import grokcore.component as grok

from zope.component import getUtilitiesFor
from zope.interface import implements
from zope.event import notify

from pika import PlainCredentials, ConnectionParameters, AsyncoreConnection

from affinitic.zamqp.interfaces import\
    IBrokerConnection, IBeforeBrokerConnectEvent

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

    userid = "guest"
    password = "guest"

    heartbeat = 0
    tx_select = None

    def __init__(self, hostname=None, port=None, virtual_host=None,
                 userid=None, password=None, heartbeat=None, tx_select=None):

        self._sync_queue_of_failed_messages = None  # used with tx_select

        # Allow class variables to provide defaults
        self.hostname = hostname or self.hostname
        self.port = port or self.port
        self.virtual_host = virtual_host or self.virtual_host

        self.userid = userid or self.userid
        self.password = password or self.password

        if heartbeat is not None:
            self.heartbeat = heartbeat

        if tx_select is not None:
            self.tx_select = tx_select

        self.connection = None
        self.channel = None

        self._on_channel_open_callbacks = []

    def connect(self):
        credentials = PlainCredentials(
            self.userid, self.password, erase_on_connect=False)
        parameters = ConnectionParameters(
            self.hostname, self.port, self.virtual_host,
            credentials=credentials,
            heartbeat=bool(self.heartbeat))
        # FIXME: Without this, pika 0.9.5 forces interval to 1 second
        if parameters.heartbeat:
            parameters.heartbeat = int(self.heartbeat)
        self.connection = AsyncoreConnection(
            parameters=parameters,
            on_open_callback=self.on_async_connect)

        # FIXME: SimpleReconnectionStrategy doesn't work in pika 0.9.5
        # strategy = SimpleReconnectionStrategy()
        # self._async_connection = SelectConnection(
        #     parameters=parameters,
        #     on_open_callback=self.on_async_connect,
        #     reconnection_strategy=strategy)

    def add_on_channel_open_callback(self, callback):
        self._on_channel_open_callbacks.append(callback)

    @property
    def ioloop(self):
        return self.connection.ioloop

    def add_timeout(self, callback, timeout):
        return self.connection.add_timeout(callback, timeout)

    def on_async_connect(self, connection):
        print "ON ASYNC_CONNECT"
        self.connection.channel(self.on_async_channel_open)

    def on_async_channel_open(self, channel):
        print "ON ASYNC_CHANNEL_OPEN"
        self.channel = channel
        if self.tx_select:  # should channel be transactional
            channel.tx_select(self.on_async_channel_tx_select)
        else:
            for callback in self._on_channel_open_callbacks:
                callback(self.channel)

    def on_async_channel_tx_select(self, frame):
        for callback in self._on_channel_open_callbacks:
            callback(self.channel)


class BeforeBrokerConnectEvent(object):
    implements(IBeforeBrokerConnectEvent)


def init(self):
    notify(BeforeBrokerConnectEvent())
    for connection_id, connection in getUtilitiesFor(IBrokerConnection):
        connection.connect()

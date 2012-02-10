# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""

# XXX: Monkey patch bug https://github.com/pika/pika/issues/113 in 0.9.5
import pika.adapters.blocking_connection
from pika import log
setattr(pika.adapters.blocking_connection, 'log', log)

import grokcore.component as grok

from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import implementedBy

from pika import PlainCredentials, ConnectionParameters, SelectConnection
from pika.reconnection_strategies import SimpleReconnectionStrategy

from pika import BlockingConnection as BlockingConnectionBase
from pika.adapters import BaseConnection
from pika.adapters.blocking_connection import SOCKET_TIMEOUT

from affinitic.zamqp.interfaces import\
    IBrokerConnection, IBrokerConnectionFactory

import logging
logger = logging.getLogger('affinitic.zamqp')


class BlockingConnection(BlockingConnectionBase):
    __doc__ = BlockingConnectionBase.__doc__

    def _adapter_connect(self, host, port):
        BaseConnection._adapter_connect(self, host, port)
        self.socket.setblocking(1)
        self.socket.settimeout(SOCKET_TIMEOUT)
        self._socket_timeouts = 0
        self._on_connected()
        self._timeouts = dict()

        # XXX: Original version loops until self.is_open without reconnecting,
        # that is forever if the broker was down when the loop started. This
        # may not be safe either, but just letting this go, seems to allow
        # reconnections later on.
        trials = 3
        while not self.is_open and trials > 0:
            self._flush_outbound()
            self._handle_read()
            trials -= 1
        return self


class SyncReconnectionStrategy(SimpleReconnectionStrategy):
    """
    Pika reconnection strategy for blocking connection.

    Reconnection strategy is initiated as soon as an exception from socket.send
    has been raised. Unfortunately, we cannot reconnect in the middle of
    message delivering sequence. We can only set a flag for reconnection and
    the client must call our reconnect as soon as its possible.
    """

    def on_connection_closed(self, conn):
        setattr(conn, '_reconnect_request', True)  # set reconnection flag

    def reconnect(self, conn):
        if getattr(conn, '_reconnect_request', False):
            delattr(conn, '_reconnect_request')  # clear reconnection flag

            logger.error('%s retrying %r once now (%r attempts)',
                        self.__class__.__name__, conn.parameters,
                        self.attempts_since_last_success)

            conn.outbound_buffer.flush()  # flush buffer; start from scratch
            conn._reconnect()  # try to reconnect


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
        """Returns a synchronous connection. Creates a new connection
        or reconnects closed connection when required."""
        if not self._sync_connection:
            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials)
            strategy = SyncReconnectionStrategy()
            self._sync_connection = BlockingConnection(
                parameters=parameters, reconnection_strategy=strategy)

        # Reconnect when required
        if getattr(self._sync_connection, '_reconnect_request', False):
            self._sync_connection.reconnection.reconnect(self._sync_connection)
            if self._sync_channel:  # Destroy the old channel
                del self._sync_channel
                self._sync_channel = None

        return self._sync_connection

    @property
    def is_open(self):
        """Returns the state of known state of the synchronous connection
        without trying to re-establish the connection"""
        return self._sync_connection.is_open

    @property
    def channel(self):
        """Returns a synchronous channel. Creates a new connection
        or reconnects closed connection when required."""
        assert self.connection  # connect/reconnect when required
        if not self._sync_channel:
            self._sync_channel = self.connection.channel()
            if self.tx_select:  # should channel be transactional
                self._sync_channel.tx_select()
        return self._sync_channel

    def async_connect(self, on_channel_open):
        if not self._async_connection or not self._async_connecting:
            self._async_connecting = True
            self._async_channel_open_callback = on_channel_open

            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials)
            self._async_connection = SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_async_connect)

            # FIXME: SimpleReconnection strategy doesn't work on pika 0.9.5
            # strategy = SimpleReconnectionStrategy()
            # self._async_connection = SelectConnection(
            #     parameters=parameters,
            #     on_open_callback=self.on_async_connect,
            #     reconnection_strategy=strategy)

    def on_async_connect(self, connection):
        self._async_connecting = False
        self._async_connection = connection
        self._async_connection.channel(self._async_channel_open_callback)

    def on_async_channel_open(self, channel):
        self._async_channel_open_callback(channel)

    @property
    def async_ioloop(self):
        return self._async_connection.ioloop


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

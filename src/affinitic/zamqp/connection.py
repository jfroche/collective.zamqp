# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""

# XXX: Monkey patch bug https://github.com/pika/pika/issues/113 in 0.9.5
import pika.adapters.blocking_connection
from pika import log
setattr(pika.adapters.blocking_connection, 'log', log)

import grokcore.component as grok

from zope.component import getUtility
from zope.component.interfaces import IFactory
from zope.interface import implementedBy

from socket import error as SocketError

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

        # XXX: The original version loops forever (until self.is_open) without
        # trying to reconnect if the broker was down when the loop started.
        # Limiting the loop and just letting the connection process to continue
        # seems to allow reconnections later on.
        trials = 3
        while not self.is_open and trials > 0:
            self._flush_outbound()
            self._handle_read()
            trials -= 1
        return self


class BlockingReconnectionStrategy(SimpleReconnectionStrategy):
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
            try:
                conn._reconnect()  # try to reconnect
            except SocketError as e:
                logger.error(e)


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

    heartbeat = 0
    tx_select = None

    def __init__(self, hostname=None, port=None, virtual_host=None,
                 userid=None, password=None, heartbeat=None, tx_select=None,
                 on_channel_open=None):

        self._sync_connection = None
        self._sync_channel = None

        self._async_connection = None
        self._async_channel = None
        self._async_channel_open_callback = None

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

        if on_channel_open:  # prepare async connection
            self._async_channel_open_callback = on_channel_open
            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials,
                heartbeat=bool(self.heartbeat))
            # FIXME: Without this, pika 0.9.5 forces interval to 1 second
            if parameters.heartbeat:
                parameters.heartbeat = int(self.heartbeat)
            self._async_connection = SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_async_connect)

            # FIXME: SimpleReconnectionStrategy doesn't work in pika 0.9.5
            # strategy = SimpleReconnectionStrategy()
            # self._async_connection = SelectConnection(
            #     parameters=parameters,
            #     on_open_callback=self.on_async_connect,
            #     reconnection_strategy=strategy)

    @property
    def sync_connection(self):
        """Returns a synchronous connection. Creates a new connection
        or reconnects closed connection when required."""
        if not self._sync_connection:
            credentials = PlainCredentials(
                self.userid, self.password, erase_on_connect=False)
            parameters = ConnectionParameters(
                self.hostname, self.port, self.virtual_host,
                credentials=credentials,
                heartbeat=bool(self.heartbeat))
            # XXX: Without this, pika forces interval to 1 second
            if parameters.heartbeat:
                parameters.heartbeat = int(self.heartbeat)
            strategy = BlockingReconnectionStrategy()
            try:
                self._sync_connection = BlockingConnection(
                    parameters=parameters,
                    reconnection_strategy=strategy)
            except SocketError as e:
                logger.error(e)

        # Reconnect when required
        if getattr(self._sync_connection, '_reconnect_request', False):
            self._sync_connection.reconnection.reconnect(self._sync_connection)
            if self._sync_channel:  # Destroy the old channel
                del self._sync_channel
                self._sync_channel = None

        return self._sync_connection

    @property
    def sync_is_open(self):
        """Returns the state of known state of the synchronous connection
        without trying to re-establish the connection"""
        return self._sync_connection and self._sync_connection.is_open

    @property
    def sync_channel(self):
        """Returns a synchronous channel. Creates a new connection
        or reconnects closed connection when required."""
        if self.sync_connection:
            if not self._sync_channel:
                self._sync_channel = self.sync_connection.channel()
                if self.tx_select:  # should channel be transactional
                    self._sync_channel.tx_select()
            return self._sync_channel
        return None

    @property
    def async_ioloop(self):
        return self._async_connection.ioloop

    def async_add_timeout(self, callback, timeout):
        return self._async_connection.add_timeout(callback, timeout)

    def on_async_connect(self, connection):
        print "XXXXXXXXXXXXXXXXXXXXXXXXXX ON ASYN CCONNECT!"
        self._async_connection.channel(self.on_async_channel_open)

    def on_async_channel_open(self, channel):
        self._async_channel = channel
        if self.tx_select:  # should channel be transactional
            channel.tx_select(self.on_async_channel_tx_select)
        else:
            self._async_channel_open_callback(self._async_channel)

    def on_async_channel_tx_select(self, frame):
        self._async_channel_open_callback(self._async_channel)


class BrokerConnectionFactory(object):
    grok.implements(IBrokerConnectionFactory)

    title = u'BrokerConnection Factory'
    description = u'Help creating a new Broker connection'

    def getInterfaces(self):
        return implementedBy(BrokerConnection)

    def __call__(self, connection_id, on_channel_open=None):
        klass = getUtility(IBrokerConnection, name=connection_id).__class__
        # if on_channel_open is defined, prepares also asynchronous connection
        return klass(on_channel_open=on_channel_open)

grok.global_utility(BrokerConnectionFactory,
                    provides=IFactory, name='AMQPBrokerConnection')

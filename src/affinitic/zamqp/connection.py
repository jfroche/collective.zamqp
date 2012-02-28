# -*- coding: utf-8 -*-
###
# affinitic.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright by Affinitic sprl
# Copyright (c) 2012 University of Jyväskylä
###
"""Broker connection utility base class providing Pika's AsyncoreConnection"""

import time
import random
import socket
import asyncore

import grokcore.component as grok

from zope.component import getUtilitiesFor
from zope.interface import implements
from zope.event import notify

from pika import PlainCredentials, ConnectionParameters
from pika.adapters.asyncore_connection import\
    AsyncoreConnection as AsyncoreConnectionBase
from pika.callback import CallbackManager

from affinitic.zamqp.interfaces import\
    IBrokerConnection, IBeforeBrokerConnectEvent

import logging
logger = logging.getLogger('affinitic.zamqp')


class AsyncoreTimeout(asyncore.dispatcher):

    def __init__(self, callback, timeout):
        asyncore.dispatcher.__init__(self)

        self.deadline = time.time() + timeout
        self.callback = callback

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

    def readable(self):
        if time.time() > self.deadline:
            self.close()
            self.callback()
        return False

    def handle_connect(self):
        pass

    def handle_read(self):
        return True

    def handle_write(self):
        return True

    def writable(self):
        return False

    def handle_error(self):
        pass


class AsyncoreConnection(AsyncoreConnectionBase):
    __doc__ = AsyncoreConnectionBase.__doc__

    def _adapter_disconnect(self):
        """
        Called if we are forced to disconnect for some reason from Connection
        """
        # Remove from the IOLoop
        self.ioloop.stop()

        # Close our socket
        self.socket.close()

        # Close up our Connection state
        self._on_connection_closed(None, True)

    def _handle_disconnect(self):
        """
        Called internally when we know our socket is disconnected already
        """
        # Remove from the IOLoop
        self.ioloop.stop()

        # Close up our Connection state
        self._on_connection_closed(None, True)


class BrokerConnection(grok.GlobalUtility):
    """Connection utility base class"""

    grok.implements(IBrokerConnection)
    grok.baseclass()

    hostname = "localhost"
    port = 5672
    virtual_host = "/"

    username = "guest"
    password = "guest"

    heartbeat = 0
    tx_select = None

    def __init__(self, hostname=None, port=None, virtual_host=None,
                 username=None, password=None, heartbeat=None, tx_select=None):

        # allow class variables to provide defaults
        self.hostname = hostname or self.hostname
        self.port = port or self.port
        self.virtual_host = virtual_host or self.virtual_host

        self.username = username or self.username
        self.password = password or self.password

        if heartbeat is not None:
            self.heartbeat = heartbeat

        if tx_select is not None:
            self.tx_select = tx_select

        self._callbacks = CallbackManager()
        self._reconnection_delay = 1.0

        # BBB for affinitic.zamqp
        if getattr(self, "userid", None):
            from zope.deprecation import deprecated
            self.username = self.userid
            self.userid =\
                deprecated(self.userid,
                           ('Connection.userid is no more. '
                            'Please, use Connection.username instead.'))

    def connect(self):
        credentials = PlainCredentials(
            self.username, self.password, erase_on_connect=False)
        parameters = ConnectionParameters(
            self.hostname, self.port, self.virtual_host,
            credentials=credentials)
            # heartbeat=self.heartbeat)
        # FIXME: ^ heartbeat is buggy in pika 0.9.5
        self._connection = AsyncoreConnection(
            parameters=parameters,
            on_open_callback=self.on_async_connect)
        self._connection.add_on_close_callback(self.reconnect)

    def reconnect(self, conn):
        connection_id =\
            getattr(self, 'grokcore.component.directive.name', 'connection')
        logger.info("Trying to reconnect %s in %s seconds",
                    connection_id, self._reconnection_delay)
        self._timeout = AsyncoreTimeout(self.connect, self._reconnection_delay)
        self._reconnection_delay *= (random.random() * 0.5) + 1.0
        if self._reconnection_delay >= 60.0:
            self._reconnection_delay = 60.0

    @property
    def is_open(self):
        return getattr(self._connection, "is_open", False)

    def add_on_channel_open_callback(self, callback):
        self._callbacks.add(0, "_on_channel_open", callback, False)

    def on_async_connect(self, connection):
        self._connection = connection
        self._connection.channel(self.on_async_channel_open)
        self._reconnection_delay = 1.0
        self._timeout = None

    def on_async_channel_open(self, channel):
        self._channel = channel
        if self.tx_select:
            channel.tx_select(self.on_async_channel_tx_select)
        else:
            self._callbacks.process(0, "_on_channel_open", self, self._channel)

    def on_async_channel_tx_select(self, frame):
        self._callbacks.process(0, "_on_channel_open", self, self._channel)


class BeforeBrokerConnectEvent(object):
    implements(IBeforeBrokerConnectEvent)


def connect_all(self):
    """Connect all connections, which have related utilities registered"""

    # Notify all, who want to register callbacks for connections
    notify(BeforeBrokerConnectEvent())

    # Gather all producer and consumer utility registrations
    from affinitic.zamqp.interfaces import IProducer, IConsumer
    regs = list(getUtilitiesFor(IProducer)) + list(getUtilitiesFor(IConsumer))

    # Connect all connections, which have related utilities registered
    for connection_id, connection in getUtilitiesFor(IBrokerConnection):
        if filter(lambda reg: reg[1].connection_id == connection_id, regs):
            connection.connect()

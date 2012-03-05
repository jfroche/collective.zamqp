# -*- coding: utf-8 -*-
###
# collective.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright (c) 2012 University of Jyväskylä
###
"""ZConfig datatype support for AMQP Consuming Server"""


class BrokerConnectionFactory(object):

    def __init__(self, section):
        self.connection_id = section.connection_id

        self.hostname = section.hostname
        self.port = section.port
        self.virtual_host = section.virtual_host

        self.username = section.username
        self.password = section.password

        self.heartbeat = section.heartbeat
        self.tx_select = section.tx_select

        # Just in case, mimic ZServer.datatypes.ServerFactory
        self.ip = self.host = None

    def prepare(self, defaulthost='', dnsresolver=None,
                module=None, env=None, portbase=None):
        return

    def servertype(self):
        return "AMQP Broker Connection"

    def create(self):
        from zope.component import provideUtility

        from collective.zamqp.interfaces import IBrokerConnection
        from collective.zamqp.connection import BrokerConnection

        connection = BrokerConnection(connection_id=self.connection_id,
                                      hostname=self.hostname,
                                      port=self.port,
                                      virtual_host=self.virtual_host,
                                      username=self.username,
                                      password=self.password,
                                      heartbeat=self.heartbeat,
                                      tx_select=self.tx_select)

        provideUtility(connection, IBrokerConnection, name=self.connection_id)

        return connection


class ConsumingServerFactory(object):

    def __init__(self, section):
        self.connection_id = section.connection_id
        self.site_id = section.site_id
        self.user_id = section.user_id or 'Anonymous User'

        # Just in case, mimic ZServer.datatypes.ServerFactory
        self.ip = self.host = self.port = None

    def prepare(self, defaulthost='', dnsresolver=None,
                module=None, env=None, portbase=None):
        return

    def servertype(self):
        return "AMQP Consuming Server"

    def create(self):
        from collective.zamqp.server import ConsumingServer
        from ZServer.AccessLogger import access_logger

        return ConsumingServer(self.connection_id,
                               self.site_id,
                               self.user_id,
                               access_logger)

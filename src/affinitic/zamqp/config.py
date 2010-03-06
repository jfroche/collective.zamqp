# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from ZServer.datatypes import ServerFactory
from affinitic.zamqp.server import ZAMQPConsumerServer


class ZAMQPConsumerFactory(ServerFactory):
    """Open a storage configured via ZConfig"""

    def __init__(self, section):
        self.user = section.user
        self.host = section.host
        self.amqpconnection = section.amqpconnection
        self.password = section.password
        self.sitepath = section.sitepath

    def create(self):
        return ZAMQPConsumerServer(self.user, self.password, self.host, self.amqpconnection, self.sitepath)

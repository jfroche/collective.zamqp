# -*- coding: utf-8 -*-
###
# collective.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright (c) 2012 University of Jyväskylä
###
"""ZConfig datatype support for AMQP Consuming Server"""

from ZServer.datatypes import ServerFactory


class ConsumingServerFactory(ServerFactory):

    def __init__(self, section):
        ServerFactory.__init__(self)

        self.connection_id = section.connection_id
        self.site_id = section.site_id
        self.user_id = section.user_id or 'Anonymous User'

    def create(self):
        from collective.zamqp.server import ConsumingServer
        from ZServer.AccessLogger import access_logger

        return ConsumingServer(self.connection_id,
                               self.site_id,
                               self.user_id,
                               access_logger)

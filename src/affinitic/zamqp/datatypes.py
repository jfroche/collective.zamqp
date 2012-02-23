##############################################################################
#
# Based on ZopeClockServer by
#
# Copyright (c) 2005 Chris McDonough
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZConfig datatype support for ConsumingServer"""

from ZServer.datatypes import ServerFactory


class ConsumingServerFactory(ServerFactory):

    def __init__(self, section):
        ServerFactory.__init__(self)

        self.connection_id = section.connection_id
        self.site_id = section.site_id
        self.user_id = getattr(section, 'user_id', 'Anonymous User')

        self.host = None # appease configuration machinery

    def create(self):
        from affinitic.zamqp.server import ConsumingServer
        from ZServer.AccessLogger import access_logger
        return ConsumingServer(self.connection_id, self.site_id, self.user_id,
                               access_logger)

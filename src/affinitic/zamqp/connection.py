# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import grokcore.component as grok
from carrot.connection import BrokerConnection as CarrotBrokerConnection
from affinitic.zamqp.interfaces import IBrokerConnection


class BrokerConnection(grok.GlobalUtility, CarrotBrokerConnection):
    grok.implements(IBrokerConnection)
    grok.baseclass()

    def __init__(self, hostname=None, userid=None, password=None,
                 virtual_host=None, port=None, **kwargs):
        self._closed = None
        self._connection = None

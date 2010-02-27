# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface
import grokcore.component as grok
from zope.component import provideHandler

from affinitic.zamqp.interfaces import IConsumer, IArrivedMessage


class IFeedMessage(Interface):
    """
    Feed Message marker interface
    """


class FeedConsumer(grok.GlobalUtility):
    grok.implements(IConsumer)
    grok.name('feed')
    exchange = 'feed'
    exchangeType = 'direct'
    routingKey = 'importer'
    connectionId = 'test'
    auto_delete = False
    messageInterface = IFeedMessage

    def as_dict(self):
        return {'exchange': self.exchange,
                'routing_key': self.routingKey}


def handleMessage(message, event):
    import pdb;pdb.set_trace()

provideHandler(handleMessage, (IFeedMessage, IArrivedMessage))

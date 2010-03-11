# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from affinitic.zamqp.interfaces import IMessageWrapper, IMessage
from affinitic.zamqp.transactionmanager import VTM
import grokcore.component as grok


class MessageWrapper(grok.Adapter, VTM):
    """
    """
    grok.context(IMessage)
    grok.implements(IMessageWrapper)

    def __init__(self, message):
        super(MessageWrapper, self).__init__(message)
        self.acknoledged = False

    def ack(self):
        print 'mark as ack'
        self.acknoledged = True

    def _finish(self):
        print 'finish transaction'
        if self.acknoledged:
            print 'send ack'
            self.context.ack()

    def __getattr__(self, name):
        try:
            return super(MessageWrapper, self).__getattr__(name)
        except AttributeError:
            return getattr(self.context, name)

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

    acknoledged = False

    def ack(self):
        self.acknoledged = True
        if not self.registered():
            self._ackMessage()

    def _ackMessage(self):
        self.context.ack()

    def _finish(self):
        if self.acknoledged:
            self._ackMessage()

    def _abort(self):
        self.acknoledged = False

    def __getattr__(self, name):
        try:
            return super(MessageWrapper, self).__getattr__(name)
        except AttributeError:
            return getattr(self.context, name)

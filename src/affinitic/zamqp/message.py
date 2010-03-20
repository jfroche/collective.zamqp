# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from affinitic.zamqp.interfaces import IMessageWrapper, IMessage
from affinitic.zamqp.transactionmanager import VTM
import grokcore.component as grok


class MessageWrapper(grok.Adapter, VTM):
    """
    A message wrapper that can be transaction aware
    """
    grok.context(IMessage)
    grok.implements(IMessageWrapper)

    acknowledged = False

    def ack(self):
        """
        Mark the message as acknowledge.

        If the message is registered in a transaction, we defer transmition of acknowledgement.

        If the message is not registered in a transaction, we transmit acknowledgement.
        """
        self.acknowledged = True
        if not self.registered():
            self._ackMessage()

    def _ackMessage(self):
        """
        Transmit acknowledgement to the message broker
        """
        self.context.ack()

    def _finish(self):
        if self.acknowledged:
            self._ackMessage()

    def _abort(self):
        self.acknowledged = False

    def __getattr__(self, name):
        try:
            return super(MessageWrapper, self).__getattr__(name)
        except AttributeError:
            return getattr(self.context, name)

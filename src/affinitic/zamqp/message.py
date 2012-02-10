# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import grokcore.component as grok

from zope.interface import implements, implementedBy
from zope.component import IFactory

from affinitic.zamqp.interfaces import IMessage, IMessageFactory
from affinitic.zamqp.transactionmanager import VTM


class Message(object, VTM):
    """
    A message that can be transaction aware
    """
    implements(IMessage)

    channel = None
    method_frame = None
    header_frame = None
    body = None

    acknowledged = False

    def __init__(self, channel, method_frame, header_frame, body):
        self.channel = channel
        self.method_frame = method_frame
        self.header_frame = header_frame

        # FIXME: de-serialize body
        self.body = body

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
        # self.channel.ack()

    def _finish(self):
        if self.acknowledged:
            self._ackMessage()

    def _abort(self):
        self.acknowledged = False

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)
        else:
            return getattr(self.body, name)

    def sortKey(self, *ignored):
        "Always be the last one !"
        return '~zamqp 9'


class MessageFactory(object):
    grok.implements(IMessageFactory)

    title = u'Message Factory'
    description = u'Help creating a new message'

    def getInterfaces(self):
        return implementedBy(Message)

    def __call__(self, channel, method_frame, header_frame, body):
        return Message(channel, method_frame, header_frame, body)

grok.global_utility(MessageFactory,
                    provides=IFactory, name='AMQPMessage')

# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright 2010-2011 by Affinitic sprl
Copyright 2012 by University of Jyväskylä
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

    state = None

    channel = None
    method_frame = None
    header_frame = None
    body = None

    def __init__(self, channel, method_frame, header_frame, body):
        self.channel = channel
        self.method_frame = method_frame
        self.header_frame = header_frame

        # FIXME: de-serialize body
        self.body = body

        self.state = "RECEIVED"
        self._should_ack = False

    def ack(self):
        """
        Mark the message as acknowledge.

        If the message is registered in a transaction, we defer transmition of
        acknowledgement.

        If the message is not registered in a transaction, we transmit
        acknowledgement.
        """
        self._should_ack = True
        if not self.registered():
            self._ack()

    def _ack(self):
        """
        Transmit acknowledgement to the message broker
        """
        self.state = "ACK"
        self.channel.basic_ack(
            delivery_tag=self.method_frame.delivery_tag)
        print "ACK for", self.method_frame.delivery_tag

    def _finish(self):
        if self._should_ack:
            self._ack()

    def _abort(self):
        self._should_ack = False

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            return object.__getattribute__(self, name)
        else:
            return getattr(self.body, name)

    def sortKey(self, *ignored):
        return '~zamqp 9'  # Always be the last one!


class MessageFactory(object):
    grok.implements(IMessageFactory)

    title = u'Message Factory'
    description = u'Help creating a new message'

    def getInterfaces(self):
        return implementedBy(Message)

    def __call__(self, channel, method_frame, header_frame, body):
        return Message(channel, method_frame, header_frame, body)

grok.global_utility(MessageFactory, provides=IFactory, name='AMQPMessage')

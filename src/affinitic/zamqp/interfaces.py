# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent


class IAMQPConnection(Interface):
    """
    AMQP Broker connection to an AMQP server via a specific virtual host
    """

    id = Attribute('')

    hostname = Attribute('')

    port = Attribute('')

    userid = Attribute('')

    password = Attribute('')

    virtualHost = Attribute('')

    def getConnection():
        """
        Return a connection to access a virtual host
        """


class IConsumer(Interface):
    """
    A Consumer receive messages sent to a queue via an exchange
    """

    connectionId = Attribute('')

    queue = Attribute('')

    exchange = Attribute('')

    exchangeType = Attribute('')

    routingKey = Attribute('')

    auto_delete = Attribute('')

    messageInterface = Attribute("Return the interface related to the message")


class IArrivedMessage(IObjectEvent):
    """
    Event fired when a new message has arrived
    """

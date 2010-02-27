# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface, Attribute


class AMQPConnection(Interface):
    """
    AMQP Broker connection to an AMQP server via a specific virtual host
    """

    hostname = Attribute('')

    port = Attribute('')

    userid = Attribute('')

    password = Attribute('')

    virtualHost = Attribute('')

    def getConnection():
        """
        Return a connection to access a virtual host
        """


class Consumer(Interface):
    """
    A Consumer receive messages sent to a queue via an exchange
    """

    queue = Attribute('')

    exchange = Attribute('')

    routingKey = Attribute('')

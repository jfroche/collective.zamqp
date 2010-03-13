# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent, IFactory


class IBrokerConnection(Interface):
    """
    AMQP Broker connection to an AMQP server via a specific virtual host
    """

    id = Attribute('The connection id')

    hostname = Attribute('The hostname where the broker is located')

    port = Attribute('The port where the broker is running (default: 5672)')

    userid = Attribute('The user id to access the broker')

    password = Attribute("The user's password to access the broker")

    virtualHost = Attribute('The virtual host id')


class IBrokerConnectionFactory(IFactory):

    def __call__(connectionId):
        """
        Create a BrokerConnection by fetching the corresponding BrokerConnection
        with ``connectionId``

        :param connectionId: the id of the broker connection
        :rtype: BrokerConnection
        """


class IConsumer(Interface):
    """
    A Consumer receive messages sent to a queue via an exchange
    """

    connectionId = Attribute('The connection id where the queue is/will be registered')

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


class IMessageWrapper(Interface):
    """
    A Message wrapper
    """


class IMessage(Interface):
    """
    """


class IPublisher(Interface):
    """
    A Publisher send message to a queue via an exchange
    """

    connectionId = Attribute('')

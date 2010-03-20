# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
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

    connection_id = Attribute('The connection id where the queue is/will be registered')

    queue = Attribute('Name of the queue')

    exchange = Attribute('Name of the exchange the queue binds to')

    exchange_type = Attribute('')

    routing_key = Attribute('')

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

    connection_id = Attribute('The BrokerConnection id where the queue is/will be registered')


class IConsumerSet(Interface):
    """
    A Set of consumers connected to the same broker connection
    """


class IConsumerSetFactory(IFactory):

    def __call__(connectionId):
        """
        Create a ConsumerSet and link the corresponding consumers
        based on the ``connectionId``

        :param connectionId: the id of the broker connection where the consumers are connected to
        :rtype: ConsumerSet
        """

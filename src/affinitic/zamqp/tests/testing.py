# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from time import sleep
from unittest import TestSuite

from zope.interface import Interface
import grokcore.component as grok
from zope.component import provideHandler

from affinitic.zamqp.consumer import Consumer
from affinitic.zamqp.connection import BrokerConnection
from affinitic.zamqp.interfaces import IArrivedMessage


class IFeedMessage(Interface):
    """
    Feed Message marker interface
    """


class TestConnection(BrokerConnection):
    grok.name("test")
    virtual_host = "test"
    hostname = "localhost"
    port = 5672
    userid = "test"
    password = "test"


class FeedConsumer(Consumer):
    grok.name('feed')
    queue = "db.foo"
    exchange = 'db.foo'
    exchange_type = 'direct'
    routing_key = 'importer'
    connection_id = 'cerise'
    messageInterface = IFeedMessage


def handleMessage(message, event):
    print 'consuming %s' % message.payload
    sleep(20)

provideHandler(handleMessage, (IFeedMessage, IArrivedMessage))


def test_suite():
    return TestSuite()

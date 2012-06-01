# -*- coding: utf-8 -*-
"""Test utilities"""

from grokcore import component as grok

from collective.zamqp.connection import BrokerConnection
from collective.zamqp.producer import Producer


class TestConnection(BrokerConnection):
    grok.name("test.connection")


class SimpleProducer(Producer):
    grok.name("my.queue")

    connection_id = "test.connection"
    queue = "my.queue"


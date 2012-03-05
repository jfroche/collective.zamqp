# -*- coding: utf-8 -*-
"""
collective.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by University of Jyväskylä

Base classes for registering ping to keep the connection alive (in
environments, where firewalls close idle connections).

Usage
-----

1. Define producer and consumer::

    from collective.zamqp.keepalive import PingProducer, PingConsumer

    class Ping(PingProducer):
        grok.name("my.app.ping")
        connection_id = "my.app.amqp"

    class Pong(PingConsumer):
        grok.name("my.app.pong")
        connection_id = "my.app.amqp"

2. Define view to send ping message::

    from collective.zamqp.keepalive import ping

    class PingView(grok.View):
        grok.name("my-app-ping")
        grok.context(IPloneSiteRoot)
        grok.require("zope.Public")

        render = lambda self: ping("my.app.ping")

3. Define Zope clock-server to call the view once per a minute::

    <clock-server>
        method /mysite/@@my-app-ping
        period 60
        host localhost
     </clock-server>
"""

from grokcore import component as grok

from zope.interface import Interface
from zope.component import getUtility

from collective.zamqp.producer import Producer
from collective.zamqp.consumer import Consumer

from collective.zamqp.interfaces import IProducer, IMessageArrivedEvent

import logging
logger = logging.getLogger('collective.zamqp')


class IPingMessage(Interface):
    """Ping"""


class PingProducer(Producer):
    grok.baseclass()

    def set_queue(self, s):
        pass

    def get_queue(self):
        return '%s.ping' % self.connection_id

    exchange = 'collective.zamqp'
    queue = property(get_queue, set_queue)
    durable = False


class PingConsumer(Consumer):
    grok.baseclass()
    marker = IPingMessage

    def set_queue(self, s):
        pass

    def get_queue(self):
        return '%s.ping' % self.connection_id

    queue = property(get_queue, set_queue)
    durable = False
    auto_ack = True


def ping(name):
    producer = getUtility(IProducer, name=name)
    producer._register()
    producer.publish('PING')
    logger.info('PING....')


@grok.subscribe(IPingMessage, IMessageArrivedEvent)
def pong(message, event):
    logger.info('....PONG')

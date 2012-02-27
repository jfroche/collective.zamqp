# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by University of Jyväskylä

Base classes for registering ping to keep the connection alive (in
environments, where firewalls close idle connections).

Usage
-----

1. Define producer and consumer::

    from affinitic.zamqp.keepalive import PingProducer, PingConsumer

    class Ping(PingProducer):
        grok.name("my.app.ping")
        connection_id = "my.app.amqp"

    class Pong(PingConsumer):
        grok.name("my.app.pong")
        connection_id = "my.app.amqp"

2. Define view to send ping message::

    from affinitic.zamqp.keepalive import ping

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
from zope.component import getUtility, provideSubscriptionAdapter

from affinitic.zamqp.producer import Producer
from affinitic.zamqp.consumer import Consumer

from affinitic.zamqp.interfaces import IProducer, IMessageArrivedEvent

import logging
logger = logging.getLogger('affinitic.zamqp')


class IPingMessage(Interface):
    """Ping"""


class PingProducer(Producer):
    grok.baseclass()

    exchange = 'affinitic.zamqp'
    durable = False

    def set_routing_key(self, s):
        pass

    def get_routing_key(self):
        return '%s.ping' % self.connection_id

    routing_key = property(get_routing_key, set_routing_key)


class PingConsumer(Consumer):
    grok.baseclass()

    exchange = 'affinitic.zamqp'
    durable = False
    auto_delete = True
    messageInterface = IPingMessage

    def set_queue(self, s):
        pass

    def get_queue(self):
        return '%s.ping' % self.connection_id

    queue = property(get_queue, set_queue)


def ping(name):
    producer = getUtility(IProducer, name=name)
    producer._register()
    logger.info('PING')
    producer.send('PING')


def pong(message):
    logger.info('PONG')
    message.ack()

provideSubscriptionAdapter(pong, [IPingMessage], IMessageArrivedEvent)

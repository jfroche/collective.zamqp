# -*- coding: utf-8 -*-
"""
collective.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by University of Jyväskylä

Base classes for registering ping to keep the connection alive in environments,
where firewalls close idle connections. In addition, ping causes enough socket
traffic (for asyncore) to help re-connections on otherwise silent
AMQP-dedicated zeo-clients.

Usage
-----

1. Define producer and consumer::

    from collective.zamqp.keepalive import PingProducer, PingConsumer

    class Ping(PingProducer):
        grok.name("myapp.ping")
        connection_id = "myapp.amqp"

    class Pong(PingConsumer):
        grok.name("myapp.pong")
        connection_id = "myapp.amqp"

2. Define view to send ping message::

    from collective.zamqp.keepalive import ping

    class PingView(grok.View):
        grok.name("myapp-ping")
        grok.context(IPloneSiteRoot)
        grok.require("zope.Public")

        render = lambda self: ping("myapp.ping")

3. Define Zope clock-server to call the view once per a minute::

    <clock-server>
        method /mysite/@@my-app-ping
        period 60
        host localhost
    </clock-server>
"""

from grokcore import component as grok

from zope.component import getUtility

from collective.zamqp.producer import Producer
from collective.zamqp.consumer import Consumer
from collective.zamqp.interfaces import IProducer
from collective.zamqp import utils

import logging
logger = logging.getLogger('collective.zamqp')


class PingProducer(Producer):
    grok.baseclass()

    def set_queue(self, s):
        pass

    def get_queue(self):
        return '%s.%s.ping' % (utils.getBuildoutName(), self.connection_id)

    exchange = 'collective.zamqp'
    routing_key = property(get_queue, set_queue)
    queue = property(get_queue, set_queue)
    durable = False


class PingConsumer(Consumer):
    grok.baseclass()

    def set_queue(self, s):
        pass

    def get_queue(self):
        return '%s.%s.ping' % (utils.getBuildoutName(), self.connection_id)

    queue = property(get_queue, set_queue)
    durable = False

    def on_message_received(self, channel, method_frame, header_frame, body):
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        if self._tx_select:
            channel.tx_commit()  # min support for transactional channel
        logger.debug('....PONG')


def ping(name):
    producer = getUtility(IProducer, name=name)
    producer._register()
    producer.publish('PING')
    logger.debug('PING....')

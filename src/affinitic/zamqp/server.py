# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import asyncore
import socket

from ZServer.ClockServer import ClockServer, LogHelper
from ZServer.PubCore import handle
from ZServer.AccessLogger import access_logger
from carrot.messaging import Consumer
from carrot.connection import BrokerConnection


class ZAMQPConsumerServer(ClockServer):

    SERVER_IDENT = 'Zope AMQP consumer'
    _shutdown = 0

    def __init__(self, user, password, host, amqpconnection):
        asyncore.dispatcher.__init__(self)
        self.user = user
        self.password = password
        self.host = host
        self.method = 'consume'
        self.connection = amqpconnection
        self.logger = LogHelper(access_logger)
        h = self.headers = []
        h.append('User-Agent: Zope AMQP Consumer Server Client')
        h.append('Accept: text/html,text/plain')
        if not host:
            host = socket.gethostname()
        h.append('Host: %s' % host)
        auth = False
        if user and password:
            encoded = ('%s:%s' % (user, password)).encode('base64')
            h.append('Authorization: Basic %s' % encoded)
            auth = True
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.log_info('ZAMQP Consumer Server started')
        self.started = False
        self.zhandler = handle
        self.createConsumer()

    def createConsumer(self):

        def import_feed_callback(message_data, message):
            req, zreq, resp = self.get_requests_and_response()
            feed_url = message_data["import_feed"]
            print("Got feed import message for: %s" % feed_url)
            zreq.args = (message_data, message)
            self.zhandler('Zope2', zreq, resp)
        self.conn = BrokerConnection(hostname="localhost", port=5672,
                                userid="test", password="test", virtual_host="test")
        self.consumer = Consumer(connection=self.conn, queue="feed",
                            exchange="feed", routing_key="importer")
        self.consumer.register_callback(import_feed_callback)

    def readable(self):
        while 1:
            msg = self.consumer.fetch(enable_callbacks=True)
            if msg is None:
                break
        return False

    def clean_shutdown_control(self, phase, time_in_this_phase):
        if phase == 1:
            self.log_info('Shutting down ZAMQP Consumer Server')
            self.consumer.close()
            self.conn.close()

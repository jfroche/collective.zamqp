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


class ZAMQPConsumerServer(ClockServer):

    SERVER_IDENT = 'Zope AMQP consumer'
    _shutdown = 0

    def __init__(self, user, password, host, amqpconnection, sitePath):
        asyncore.dispatcher.__init__(self)
        self.user = user
        self.password = password
        self.host = host
        self.method = '%s/consume' % sitePath
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

    def readable(self):
        # generate a request at most once every self.period seconds
        if not self.started:
            req, zreq, resp = self.get_requests_and_response()
            zreq.args = (self.connection,)
            ret = self.zhandler('Zope2', zreq, resp)
            print ret
            self.started = True
        return False

    def clean_shutdown_control(self, phase, time_in_this_phase):
        if phase == 1:
            self.log_info('Shutting down ZAMQP Consumer Server')
            self.consumer.close()
            self.conn.close()

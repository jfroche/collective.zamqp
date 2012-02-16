# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import sys
import getopt

import grokcore.component as grok

from zope.component import getUtility

from affinitic.zamqp.interfaces import\
    IPublisher, IBrokerConnection, ISerializer
from affinitic.zamqp.transactionmanager import VTM

from pika import BasicProperties
from pika.exceptions import ChannelClosed

import logging
logger = logging.getLogger('affinitic.zamqp')


class Publisher(grok.GlobalUtility, VTM):
    """
    Publisher utility base class

    See `<#affinitic.zamqp.interfaces.IPublisher>`_ for more details.
    """
    grok.baseclass()
    grok.implements(IPublisher)

    connection_id = None

    exchange = None
    routing_key = None
    durable = True

    reply_to = None
    serializer = "text/plain"

    def __init__(self, connection_id=None,
                 exchange=None, routing_key=None, exchange_type=None,
                 durable=None, reply_to=None, serializer=None):

        self._connection = None
        self._queue_of_pending_messages = None
        self._queue_of_failed_messages = None  # used with tx_select

        # Allow class variables to provide defaults
        self.connection_id = connection_id or self.connection_id
        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key\
            or getattr(self, "grokcore.component.directive.name", None)

        if durable is not None:
            self.durable = durable

        self.reply_to = reply_to or self.reply_to
        self.serializer = serializer or self.serializer

    @property
    def connection(self):
        if self._connection is None:
            self._connection =\
                getUtility(IBrokerConnection, name=self.connection_id)
        return self._connection

    def send(self, message, exchange=None, routing_key=None,
             mandatory=False, immediate=False,
             content_type=None, content_encoding=None,
             headers=None, delivery_mode=None, priority=None,
             correlation_id=None, reply_to=None, expiration=None,
             message_id=None, timestamp=None, type=None, user_id=None,
             app_id=None, cluster_id=None, serializer=None):

        exchange = exchange or self.exchange
        routing_key = routing_key or self.routing_key
        reply_to = reply_to or self.reply_to
        serializer = serializer or self.serializer

        if serializer and not content_type:
            util = getUtility(ISerializer, name=serializer)
            content_type = util.content_type
            message = util.serialize(message)
        elif not content_type:
            content_type = "text/plain"

        if delivery_mode is None:
            if not self.durable:
                delivery_mode = 1  # message is transient
            else:
                delivery_mode = 2  # message is persistent

        properties = BasicProperties(
            content_type=content_type, content_encoding=content_encoding,
            headers=headers, delivery_mode=delivery_mode, priority=priority,
            correlation_id=correlation_id, reply_to=reply_to,
            expiration=expiration, message_id=message_id, timestamp=timestamp,
            type=type, user_id=user_id, app_id=app_id, cluster_id=cluster_id)

        msg = {
            "exchange": exchange,
            "routing_key": routing_key,
            "body": message,
            "properties": properties,
        }

        if self.registered():
            self._queue_of_pending_messages.append(msg)
        else:
            self._basic_publish(**msg)

    def _basic_publish(self, **kwargs):
        try:
            self.connection.sync_channel.basic_publish(**kwargs)
        except ChannelClosed:
            # Publish fails silently unless self.connection.tx_select
            pass

        if self.connection.tx_select:  # support transactional channel
            tx_commit = False
            if self.connection.sync_is_open:
                try:
                    self.connection.sync_channel.tx_commit()
                    tx_commit = True
                except KeyError:
                    pass

            if tx_commit:
                # commit succcess
                if self._queue_of_failed_messages is not None:
                    self._queue_of_pending_messages.extend(
                        self._queue_of_failed_messages)
                    logger.info("Recovered %s unsent message(s).",
                                len(self._queue_of_failed_messages))
                    self._queue_of_failed_messages = None
            else:
                # commit failed
                if self._queue_of_failed_messages is None:
                    self._queue_of_failed_messages = []
                self._queue_of_failed_messages.append(kwargs)
                logger.warning("TX_COMMIT failed (%s) for %s",
                               len(self._queue_of_failed_messages), kwargs)

    def _begin(self):
        self._queue_of_pending_messages = []
        # establish a connection even if the message might not be send, because
        # the transaction must fail when the connection cannot be established
        assert self.connection.sync_channel

    def _abort(self):
        self._queue_of_pending_messages = None

    def _finish(self):
        while self._queue_of_pending_messages:
            self._basic_publish(**self._queue_of_pending_messages.pop())


def usage():
    print """
    Usage: publishmsg [-h | -o hostname -t port -u (userid) -p (password)
           -v (virtual_host) -e (exchange) -r (routing_key) -m (message)]

    Options:

        -h / --help
            Print thiѕ help message

        -o hostname / --hostname=host
            Hostname where the message broker is running

        -t port / --port=portNumber
            Port Number of the message broker (default to 5672)

        -u userid / --user=userid
            Connection User Id

        -p password / --password=password
            Connection Password

        -v virtual_host / --virtual-host=virtual_host
            Virtual host id

        -e exchange_name / --exchange=exchange_name
            Exchange name

        -r routing_key / --routing-key=routing_key
            Routing key id

        -m message / --message=message
            Message
"""


def getCommandLineConfig():
    opts = []
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:t:u:p:v:e:r:m:",
            ["help", "hostname=", "port=", "userid=", "password=",
             "virtual-host=", "exchange=", "routing-key=", "message="])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    host = None
    port = 5672
    username = None
    password = None
    virtual_host = None
    exchange = None
    routing_key = None
    message = None
    if len(opts) == 0:
        usage()
        sys.exit(2)
    for o, value in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--hostname"):
            host = value
        elif o in ("-t", "--port"):
            port = int(value)
        elif o in ("-u", "--userid"):
            username = value
        elif o in ("-p", "--password"):
            password = value
        elif o in ("-v", "--virtual-host"):
            virtual_host = value
        elif o in ("-e", "--exchange"):
            exchange = value
        elif o in ("-r", "--routing-key"):
            routing_key = value
        elif o in ("-m", "--message"):
            message = value
    return (host, port, virtual_host, username, password,
            exchange, routing_key, message)


from pika import PlainCredentials, ConnectionParameters, SelectConnection


def main():

    class BasicPublish(object):
        """See also: http://pika.github.com/examples.html"""

        def __init__(self, host, port, virtual_host, username, password,
                     exchange, routing_key, message):
            self.channel = None
            self.exchange = exchange
            self.routing_key = routing_key
            self.message = message

            credentials = PlainCredentials(
                username, password, erase_on_connect=False)
            parameters = ConnectionParameters(
                host, port, virtual_host, credentials=credentials)

            self.connection = SelectConnection(
                parameters=parameters, on_open_callback=self.on_connect)

        def on_connect(self, connection):
            self.connection.channel(self.on_channel_open)

        def on_channel_open(self, channel):
            self.channel = channel

        ## Commented code below declares both a new exhange and a new queue and
        ## binds them together:

        #     self.channel.exchange_declare(exchange=self.exchange,
        #                                   type="direct", durable=True,
        #                                   auto_delete=False,
        #                                   callback=self.on_exchange_declared)

        # def on_exchange_declared(self, frame):
        #     self.channel.queue_declare(queue=self.routing_key, durable=True,
        #                                exclusive=False, auto_delete=False,
        #                                callback=self.on_queue_declared)

        # def on_queue_declared(self, frame):
        #     self.channel.queue_bind(exchange=self.exchange,
        #                             queue=self.routing_key,
        #                             # routing_key=self.routing_key,
        #                             callback=self.on_queue_bound)

        # def on_queue_bound(self, frame):
            properties = BasicProperties(content_type="text/plain",
                                         delivery_mode=1)
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=self.routing_key,
                                       body=self.message,
                                       properties=properties)
            self.connection.close()

    basic_publish = BasicPublish(*getCommandLineConfig())
    try:
        basic_publish.connection.ioloop.start()
    except KeyboardInterrupt:
        basic_publish.connection.close()
        basic_publish.connection.ioloop.start()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
import sys
import getopt

import grokcore.component as grok

from zope.component import getUtility, queryUtility

from affinitic.zamqp.interfaces import IPublisher, IBrokerConnection
from affinitic.zamqp.transactionmanager import VTM


class Publisher(grok.GlobalUtility, VTM):
    """
    Publisher utility

    See `<#affinitic.zamqp.interfaces.IPublisher>`_ for more details.
    """
    grok.baseclass()
    grok.implements(IPublisher)

    connection_id = None

    def __init__(self):
        self._queueOfPendingMessage = None

    # def __init__(self, connection=None, exchange=None, routing_key=None,
    #              exchange_type=None, durable=None, auto_delete=None,
    #              channel=None, **kwargs):

    #     if connection:
    #         self._connection = connection
    #     else:
    #         self._connection =\
    #             queryUtility(IBrokerConnection, name=self.connection_id)

    #     # Allow class variables to provide defaults
    #     exchange = exchange or getattr(self, "exchange", None)
    #     routing_key = routing_key or getattr(self, "routing_key", None)
    #     exchange_type = exchange_type or getattr(self, "exchange_type", None)
    #     durable = durable or getattr(self, "durable", None)
    #     auto_delete = auto_delete or getattr(self, "auto_delete", None)

    #     serializer = kwargs.get("serializer",
    #                             getattr(self, "serializer", None))
    #     auto_declare = kwargs.get("auto_declare",
    #                               getattr(self, "auto_declare", None))
    #     kwargs.update({
    #         "serializer": serializer,
    #         "auto_declare": auto_declare
    #         })

    #     if self._connection:
    #         super(Publisher, self).__init__(
    #             self._connection, exchange, routing_key, exchange_type,
    #             durable, auto_delete, channel, **kwargs)
    #     else:
    #         kwargs.update({
    #             "exchange": exchange, "routing_key": routing_key,
    #             "exchange_type": exchange_type, "durable": durable,
    #             "auto_delete": auto_delete
    #             })
    #         self._lazy_init_kwargs = kwargs

    # @property
    # def connection(self):
    #     if self._connection is None:
    #         # perform lazy init when connection is needed for the first time
    #         self._connection =\
    #             getUtility(IBrokerConnection, name=self.connection_id)
    #         super(Publisher, self).__init__(
    #             self._connection, **self._lazy_init_kwargs)
    #     return self._connection

    def send(self, message_data, routing_key=None, delivery_mode=None,
            mandatory=False, immediate=False, priority=0, content_type=None,
            content_encoding=None, serializer=None):
        if self.registered():
            msgInfo = {'data': message_data,
                       'info': {'routing_key': routing_key,
                                'delivery_mode': delivery_mode,
                                'mandatory': mandatory,
                                'immediate': immediate,
                                'priority': priority,
                                'content_type': content_type,
                                'content_encoding': content_encoding,
                                'serializer': serializer}}
            self._queueOfPendingMessage.append(msgInfo)
        else:
            self._sendToBroker(
                message_data, routing_key, delivery_mode, mandatory,
                immediate, priority, content_type, content_encoding,
                serializer)

    def _sendToBroker(self, *args, **kwargs):
        import pdb; pdb.set_trace()

    def _begin(self):
        self._queueOfPendingMessage = []

        # # establish a connection even if the message might not be send directly
        # self.connection

    def _abort(self):
        self._queueOfPendingMessage = None

    def _finish(self):
        for msgInfo in self._queueOfPendingMessage:
            message_data = msgInfo['data']
            sendInfo = msgInfo['info']
            self._sendToBroker(message_data, **sendInfo)


def usage():
    print """
    Usage: publishmsg [-h | -o hostname -t port -u (userid) -p (password) -v (virtual_host) -e (exchange) -r (routing_key) -m (message)]

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
            ["help", "hostname=", "port=", "userid=", "password=", "virtual-host=",
             "exchange=", "routing-key=", "message="])
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


from pika import\
    PlainCredentials, ConnectionParameters, SelectConnection,\
    BasicProperties


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

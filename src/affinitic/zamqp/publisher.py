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
from zope.component import getUtility

from carrot.connection import BrokerConnection
from carrot.messaging import Publisher as CarrotPublisher

from affinitic.zamqp.interfaces import IPublisher, IBrokerConnection
from affinitic.zamqp.transactionmanager import VTM


class Publisher(grok.GlobalUtility, CarrotPublisher, VTM):
    __doc__ = CarrotPublisher.__doc__
    grok.baseclass()
    grok.implements(IPublisher)
    connection_id = None

    def __init__(self, connection=None, exchange=None, routing_key=None, **kwargs):
        self._connection = connection
        self.exchange = exchange or self.exchange
        self.routing_key = routing_key or self.routing_key
        self.delivery_mode = kwargs.get("delivery_mode", self.delivery_mode)
        self.delivery_mode = self.DELIVERY_MODES.get(self.delivery_mode,
                                                     self.delivery_mode)
        self.exchange_type = kwargs.get("exchange_type", self.exchange_type)
        self.durable = kwargs.get("durable", self.durable)
        self.auto_delete = kwargs.get("auto_delete", self.auto_delete)
        self.serializer = kwargs.get("serializer", self.serializer)
        self.auto_declare = kwargs.get("auto_declare", self.auto_declare)
        self._closed = False
        self._backend = None
        self._closed = False
        self._queueOfPendingMessage = None

    def _begin(self):
        self._queueOfPendingMessage = []
        # establish a connection even if the message might
        # not be send directly
        backend = self.backend

    _sendToBroker = CarrotPublisher.send

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
            self._sendToBroker(message_data, routing_key, delivery_mode,
                               mandatory, immediate, priority, content_type,
                               content_encoding, serializer)

    send.__doc__ = CarrotPublisher.send.__doc__

    def _finish(self):
        for msgInfo in self._queueOfPendingMessage:
            message_data = msgInfo['data']
            sendInfo = msgInfo['info']
            self._sendToBroker(message_data, **sendInfo)

    def _abort(self):
        self._queueOfPendingMessage = None

    @property
    def connection(self):
        if self._connection is None:
            self._connection = getUtility(IBrokerConnection, name=self.connection_id)
        return self._connection

    def getBackend(self):
        if self._backend is None:
            self._backend = self.connection.create_backend()
            if self.auto_declare:
                self.declare()
        return self._backend

    def setBackend(self, backend):
        self._backend = backend
        self.declare()

    backend = property(getBackend, setBackend)


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
    hostname = None
    port = 5672
    userId = None
    password = None
    virtualHost = None
    exchangeName = None
    routingKey = None
    message = None
    if len(opts) == 0:
        usage()
        sys.exit(2)
    for o, value in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--hostname"):
            hostname = value
        elif o in ("-t", "--port"):
            port = value
        elif o in ("-u", "--userid"):
            userId = value
        elif o in ("-p", "--password"):
            password = value
        elif o in ("-v", "--virtual-host"):
            virtualHost = value
        elif o in ("-e", "--exchange"):
            exchangeName = value
        elif o in ("-r", "--routing-key"):
            routingKey = value
        elif o in ("-m", "--message"):
            message = value
    return (hostname, port, userId, password, virtualHost, exchangeName, routingKey, message)


def main():
    hostname, port, userId, password, virtualHost, exchangeName, routingKey, message = getCommandLineConfig()
    conn = BrokerConnection(hostname=hostname, port=port,
                            userid=userId, password=password, virtual_host=virtualHost)
    publisher = CarrotPublisher(connection=conn, exchange=exchangeName, routing_key=routingKey)
    publisher.send(message, serializer="pickle")
    publisher.close()
    conn.close()


if __name__ == '__main__':
    main()

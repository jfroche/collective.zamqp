# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import sys
import getopt

import grokcore.component as grok
from zope.component import getUtility
from carrot.connection import BrokerConnection
from carrot.messaging import Publisher as CarrotPublisher

from affinitic.zamqp.interfaces import IPublisher, IBrokerConnection


class Publisher(grok.GlobalUtility, CarrotPublisher):
    grok.baseclass()
    grok.implements(IPublisher)

    def __init__(self):
        self._connection = None
        self._backend = None
        self._closed = False

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
        else:
            assert False, "unhandled option: %s" % o
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

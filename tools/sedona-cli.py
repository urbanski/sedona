#!/usr/bin/env python

import argparse
from twisted.internet import ssl, reactor
from twisted.internet.protocol import ClientFactory, Protocol

class EchoClient(Protocol):
    def connectionMade(self):
        print "*1\r\n$4\r\nPING\r\n"
        self.transport.write("*1\r\n$4\r\nPING\r\n")

    def dataReceived(self, data):
        print "Server said:", data
        self.transport.loseConnection()

class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()

def parse_cmd_line():
    parser = argparse.ArgumentParser(description='Sedona (Redis) command-line interface')
    parser.add_argument('host', default='127.0.0.1', type=str, help='Target server')
    parser.add_argument('port', default=6370, type=int, help='authorization file')
    parser.add_argument('-s', '--ssl', action='store_true', dest='secure', default=False, help='Use SSL')
    parser.add_argument('-u', '--user', action='store', dest='username', default=None, help='Connect with Username')
    parser.add_argument('-p', '--password', action='store_true', dest='password', default=False, help="Prompt for Password")
    parser.add_argument('-v', action='store_true', dest='verbose', default=False, help='verbose logging')
    return parser.parse_args()

if __name__ == '__main__':

    args = parse_cmd_line()

    if (args.password == True):
        password = raw_input('Password: ')

    factory = EchoClientFactory()
    reactor.connectSSL(args.host, args.port, factory, ssl.ClientContextFactory())
    reactor.run()
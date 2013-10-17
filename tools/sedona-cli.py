#!/usr/bin/env python

import argparse
import sys
from getpass import getpass
from twisted.internet import ssl, reactor
from twisted.internet.protocol import ClientFactory, Protocol

class RedisClient(Protocol):

    def buildcmd(self, *args):
        """build a redis command statement"""
        num_args = len(args)
        cmd = "*%s\r\n" % num_args
        for word in enumerate(args):
            word = word[1]
            cmd = "%s$%s\r\n%s\r\n" % (cmd,len(word), word)
        return cmd

    def connectionMade(self):
        """called when a connection is made"""
        #new connection initialized-- do we need to AUTH?
        if (self.factory.args.username != None):
            #we need to auth
            cmd = self.buildcmd("AUTH", self.factory.args.username, self.factory.args.password)
            self.transport.write(cmd)
        
        #now send a ping
        cmd = self.buildcmd("PING")
            #print "*1\r\n$4\r\nPING\r\n"
            #self.transport.write("*1\r\n$4\r\nPING\r\n")
        self.transport.write(cmd)

    def dataReceived(self, data):
        """called when data is received"""
        if data[0:1] == "+":
            #success
            print data[1:]
        #self.transport.loseConnection()

class RedisClientFactory(ClientFactory):
    protocol = RedisClient

    def __init__(self, args):
        self.args = args

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
        password = getpass('Password: ')
        args.password = password

    factory = RedisClientFactory(args)
    reactor.connectSSL(args.host, args.port, factory, ssl.ClientContextFactory())
    reactor.run()
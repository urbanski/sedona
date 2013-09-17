import logging
import re
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory

class RedisRequest():
    """handle redis request"""
    command = ""
    args = []
    debug = None
    #accept_cmds = ['ECHO']

    def __init__(self, strrequest):

        self.debug = logging.getLogger('sedona-debug')
        self.command = ""
        self.args = []

        self.debug.debug("In RedisRequest::__init__()")
        r_cmdinit = re.compile(r"\*([0-9]+)\r\n\$[0-9]+\r\n([A-Za-z]+)\r\n")
        if (r_cmdinit.match(strrequest)):
            #parse out the number of arguments in the command
            num_args = r_cmdinit.match(strrequest).group(1)
            self.num_args = int(num_args) - 1

            self.command = r_cmdinit.match(strrequest).group(2).upper()

            self.debug.debug("Command: %s" % self.command)

            #parse the args out
            r_split = re.compile(r'\$[0-9]+\r\n')
            args_el = r_split.split(strrequest)[2:]
            for arg in args_el:
                self.args.append(arg.replace("\r\n",''))
                self.debug.debug("Arg: %s" % arg.replace("\r\n",""))
        else:
            raise RedisBadCommand

class RedisResponse():
    """A redis client (string) response"""

    response_text = ""

    def __init__(self, response):
        self.response_text = response

    def __str__(self):
        response = self.response_text
        data = "$%s\r\n%s\r\n" % (len(response), response)
        return data

class RedisStatusReply():
    """returns a redis status reply"""
    response_text = ""

    def __init__(self, response):
        self.response_text = response

    def __str__(self):
        response = self.response_text
        data = "+%s\r\n" % (response)
        return data

class RedisErrorReply():
    """returns a redis error reply"""
    response_text = ""

    def __init__(self, response):
        self.response_text = response

    def __str__(self):
        response = self.response_text
        data = "-%s\r\n" % (response)
        return data

class RedisBadCommand(Exception):
    """Invalid command"""
    pass

class Redis2(Protocol):
    """Redis2 class handles the client connection throughout its duration"""

    client_socket = None
    username = ""
    authenticated = False
    userobj = None

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        """a connection has been initialized"""

        #save peer information in handler
        self._peer = self.transport.socket.getpeername()


        #set the username to default
        self.authenticated = False
        self.set_user(config['default-user'])
        self.request_count = 0


        #logger.info("%s connected from %s:%s" % (self.username, self._peer[0], self._peer[1]))
        access_logger.info("TCP/%s:%s" % (self._peer[0], self._peer[1]), extra={'user':self.username, 'ip': self._peer[0], 'command':'(CONNECT)'})

        #setup connection to the remote server
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((config['redis-host'], config['redis-port']))
        except Exception:
            logger.critical("Unable to connect to Redis (%s:%s)" % (config['redis-host'], config['redis-port']))
            #TODO: close the connection to the client

    def set_user(self, username):
        """Sets the username and grabs the appropriate user ACL"""
        debug.debug("The username for this connection is %s" % username)
        try:
            self.userobj = users[username]
            self.username = username
        except KeyError:
            ThrowCritical("No ACLs specified for user %s" % username)

        self.username = username

    def connectionLost(self, reason):
        """a connection has been lost (closed)"""
        debug.debug("Connection Lost")
        self.client_socket.close()
        pass

    def dataReceived(self, data):
        """data has been received"""
        debug.debug("Client Said: %s" % data)

        rq = None
        rq = RedisRequest(data)
        self.request_count += 1

        logger.info("%s@%s:%s %s" % (self.username, self._peer[0], self._peer[1], rq.command))

        access_logger.info(" ".join(rq.args), extra={'user':self.username, 'ip': self._peer[0], 'command':rq.command})

        #check for authentication attempt
        if (rq.command == 'AUTH'):
            #user is trying to authenticate
            debug.debug("Num Args: %s", rq.num_args)
            if (rq.num_args == 1):
                #probably a traditional AUTH request.
                #pass to the server
                self.server_raw_wrblock(data)

            elif (rq.num_args == 2):
                #Sedona auth attempt
                username = rq.args[0]
                password = rq.args[1]

                debug.debug("AUTH user: %s password: %s" % (username, password))

                #load the logger module for that user
                #find the sedona userobj for user specified in rq
                auth_response = False
                try:
                    debug.debug("Calling SedonaUser::authenticate()")
                    auth_response = users[username].authenticate(rq)
                except KeyError:
                    #use DNE, throw err
                    debug.warning("Redis2::dataReceived() KeyError thrown when looking for user account %s"
                        % username)
                    pass

                if (auth_response == True):
                    self.set_user(username)
                    self.authenticated = True
                    self.transport.write(RedisStatusReply("OK").__str__())
                else:
                    #authentication failed. rollback
                    self.transport.write(RedisErrorReply("Authentication Failed.").__str__())

            else:
                ThrowCritical("Authentication attempt received, however, %s arguments were provided?"
                    % rq.num_args)

        else:

            if (self.authenticated == False and config['require-authentication'] == True):
                #they must authenticate first
                self.transport.write(RedisErrorReply("You must authenticate first.").__str__())
            else:
                #this is not an authorization request. Proceed as normal command
                auth_response = self.userobj.authorize(rq)
                if (auth_response == SedonaACL.ACTION_ACCEPT):
                    self.server_raw_wrblock(data)
                else:
                    #not authorized. deny access
                    logger.info("Command Not Authorized.")
                    self.transport.write(RedisErrorReply("You're not authorized to run '%s'" % rq.command).__str__())

        rq = None

    def server_raw_wrblock(self, data):
        """write to the redis server and block until we get a response"""
        #send the data to the redis server directly
        self.client_socket.send(data)

        #wait for server response
        data = self.client_socket.recv(512)

        debug.debug("Server Said: %s" % data)
        self.transport.write(data)

class RedisFactory(Factory):
    """The factory for the Redis protocol"""
    def buildProtocol(self, addr):
        """setup the Redis protocol"""
        return Redis2(self)
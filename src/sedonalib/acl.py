import re
import logging

class SedonaInvalidACL(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SedonaACL():
    """a single ACL for a SedonaUser"""
    ACTION_ACCEPT = 0
    ACTION_REJECT = 1
    ACTION_DROP = 2

    command = ""
    key = None
    action = -1
    debug = None
    raw = ""

    def __init__(self, acl):
        """parse a raw (json) ACL"""
        self.acl = acl
        self.debug = logging.getLogger('sedona-debug')
        self.raw = acl
        self.debug.debug("ACL Init -- %s" % acl)
        try:
            action = self.acl['action'].upper()
            if (action == "REJECT"):
                self.action = self.ACTION_REJECT
            elif (action == "DROP"):
                self.action = self.ACTION_DROP
            else:
                self.action = self.ACTION_ACCEPT
        except KeyError:
            raise SedonaInvalidACL("An action must be specified")

        try:
            self.command = self.acl['command'].upper()
        except KeyError:
            self.command = None

        try:
            self.key = self.acl['key']
        except KeyError:
            self.key = None

        self.debug.debug("ACL: %s %s %s %s" % (self, self.command, self.key, self.action))

    def check_acl(self, request):
        """check a RedisRequest to see if it is authorized under this ACL"""
        if (self.command != None):
            if (self.command == request.command):
                self.debug.debug(self.acl)
                self.debug.debug("command %s -- key is %s" % (self.command, self.key))
                self.debug.debug(request.command)
                self.debug.debug(request.args)
                self.debug.debug(self)
                if (self.key != None):
                    #key is normally arg 1
                    self.debug.debug(request.args)
                    self.debug.debug("RE KEY: %s" % self.key)
                    self.debug.debug("RE Test: %s" % request.args[0])
                    if (re.match(self.key, request.args[0]) != None):
                        return True
                    else:
                        return False 
                return True
            else:
                return False
        else:
            return True
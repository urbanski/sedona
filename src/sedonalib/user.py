from acl import *
from nose.tools import *
import logging

class SedonaUser():
    """an object to represent a user"""

    username = ""
    acls = []
    auth_method = None
    auth_required = False
    rawkeys = {}
    auth_keys = []
    debug = None

    def __init__(self, name, json_obj):
        """parse the user json"""
        self.username = name
        self.debug = logging.getLogger('sedona-debug')
        self.acls = []

        #parse the rules
        try:
            for rule in json_obj['rules']:
                acl = SedonaACL(rule)
                self.acls.append(acl)
        except KeyError:
            #no rules for this user. This is odd
            pass
        try:
            self.auth_required = json_obj['auth_required']
        except KeyError:
            self.auth_required = False
            
        if (self.auth_required == True):
            #load additional auth methods
            self.auth_method = json_obj['auth_method']

            #load auth method, determine what other keys might be required
            self.auth_plugin = __import__("auth_%s" % self.auth_method)
            self.auth_keys = self.auth_plugin.load()
            for key in self.auth_keys:
                try:
                    t = json_obj[key]
                except KeyError:
                    ThrowCritical("Auth module '%s' requires key '%s' but it isn't set."
                        % (self.auth_method, key))
        else:
            self.auth_method = None

        self.rawkeys = json_obj

    def authorize(self, RedisRequest):
        """authorize a RedisRequest on behalf of this SedonaUser"""
        self.debug.debug("There are %s ACLs" % len(self.acls))
        for acl in self.acls:
            self.debug.debug("Evaluating ACL %s" % acl)
            acl_result = acl.check_acl(RedisRequest)
            if (acl_result == True):
                #ACL would fire for this request. Perform ACTION
                self.debug.debug("ACL action is %s" % acl.action)
                return acl.action
        return False

    def authenticate(self, rq):
        """authenticate a request against a user"""
        #assemble authkeys
        auth_data = {}
        try:
            for key in self.auth_keys:
                auth_data[key] = self.rawkeys[key]
        except KeyError:
            self.debug.debug("SedonaUser::authenticate() KeyError thrown")
        self.debug.debug("SedonaUser::authenticate() calling %s" % self.auth_plugin)
        return self.auth_plugin.authenticate(rq, auth_data)


#!/usr/bin/env python
"""
sedona
the application firewall for redis
(C) 2013 Will Urbanski
This program is released under the GNU GPLv3
"""
import socket
import logging
import sys
import re
import argparse
import json
import ConfigParser
import os

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor, ssl
from twisted.python import log

#bring in the sedona source dir
sys.path.append('/Users/will/projects/sedona/src')
from sedonalib.user import *
from sedonalib.acl import *
from sedonalib.redis import *

#global variables
config = {}
APP_VERSION = "0.0.1"


###########################
#	Application Methods   #
###########################

def parse_cmdline():
    """Handle any command line arguments"""
    parser = argparse.ArgumentParser(description='Application Firewall for Redis')
    parser.add_argument('-c', action='store', default='sedona.conf', dest='config_path', help='Configuration File')
    parser.add_argument('-a', action='store', dest='authfile', help='authorization file')
    parser.add_argument('-v', action='store_true', dest='verbose', default=False, help='verbose logging')
    return parser.parse_args()

def load_config_file(filepath):
    """load the JSON config file"""
    global REDIS_SERVER
    global REDIS_PORT

    config = ConfigParser.RawConfigParser()
    config.read(filepath)

    ini_section = 'sedona'
    server_config = {}

    #mandatory params should always exist in the config file
    mandatory_params = [
        {'name':'redis-host', 'type':'str'}, 
        {'name':'redis-port', 'type':'int'}, 
        {'name':'plaintext-port', 'type':'int'}, 
        {'name':'authfile', 'type':'str'}, 
        {'name':'default-user', 'type':'str', 'default': 'guest'},
        {'name':'ssl-support', 'type':'bool', 'default': False},
        {'name':'plaintext-support', 'type':'bool', 'default': True},
        {'name':'require-authentication', 'type':'bool', 'default': False}
        ]

    #optional params should always have a default key
    optional_params = [
        {'name': 'access-log', 'type':'str', 'default': None},
        {'name': 'debug-log', 'type':'str', 'default': None},
        {'name': 'ssl-cert-file', 'type': 'str', 'default': None},
        {'name': 'ssl-key-file', 'type': 'str', 'default': None},
        {'name': 'ssl-port', 'type': 'str', 'default': None}
    ]

    for param_dict in mandatory_params:
        try:
            if (param_dict['type'] == 'int'):
                server_config[param_dict['name']] = config.getint(ini_section, param_dict['name'])
            elif (param_dict['type'] == 'bool'):
                server_config[param_dict['name']] = config.getboolean(ini_section, param_dict['name'])
            else:
                server_config[param_dict['name']] = config.get(ini_section, param_dict['name'])
        except ConfigParser.NoOptionError as e:
            ThrowCritical(e)
        except ConfigParser.NoSectionError:
            ThrowCritical("No sedona section found in config file")

    for param_dict in optional_params:
        #set the default value
        server_config[param_dict['name']] = param_dict['default']
        
        #try to read from the config file
        try:
            if (param_dict['type'] == 'int'):
                server_config[param_dict['name']] = config.getint(ini_section, param_dict['name'])
            elif (param_dict['type'] == 'bool'):
                server_config[param_dict['name']] = config.getboolean(ini_section, param_dict['name'])
            else:
                server_config[param_dict['name']] = config.get(ini_section, param_dict['name'])
        except ConfigParser.NoOptionError as e:
            ThrowCritical(e)

    return server_config

def load_authfile(filepath):
    """load the users and authorizations file"""

    try:
        fptr = open(filepath,'r')
        json_object = json.loads(fptr.read())
        fptr.close()
    except IOError:
        ThrowCritical("Unable to read configuration file [%s]" % filepath)
    except ValueError:
        ThrowCritical("Invalid JSON [%s]" % filepath)

    ret_users = {}
    for user in json_object.keys():
        #for each user acl, initialize a user object
        uobj = SedonaUser(user, json_object[user])
        ret_users[user] = uobj

    return ret_users

def ThrowCritical(msg):
    """throw a critical error and quit"""
    logger.critical(msg)
    logger.critical("A fatal error has occured.")
    sys.exit(-1)

def print_welcome_message():
    print """
        Sedona v%s
        The Application Firewall for Redis
        https://sedona.io
    """ % (APP_VERSION)

def main():
    """the application entrypoint"""
    global config
    global users
    global logger
    global access_logger
    global debug

    #print the welcome message
    print_welcome_message()

    #handle command line arguments
    args = parse_cmdline()

    #specify verbosity
    if (args.verbose == True):
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    ## Setup Logging (generic)
    logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s %(levelname)s %(message)s')
    #logging.basicConfig(format='%(asctime)s %(clientip)s %(user)s %(levelname)s %(message)s')
    logger = logging.getLogger('sedona')
    logger.setLevel(logging.CRITICAL)

    #load the default config file
    config = load_config_file(args.config_path)

    ## Setup Debug Logging
    debug = logging.getLogger('sedona-debug')
    debug.setLevel(logging.DEBUG)
    debug.propagate = False
    fh = logging.FileHandler(config['debug-log'])
    fh.setLevel(logging.DEBUG)
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.ERROR)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)

    # add the handlers to logger
    debug.addHandler(fh)
    #debug.addHandler(ch)

    ## Setup Access logging (file-based)
    access_logger = logging.getLogger('sedona-access')
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    fh = logging.FileHandler(config['access-log'])
    fh.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s %(ip)s %(user)s %(command)s %(message)s')
    fh.setFormatter(formatter)

    # add the handlers to logger
    access_logger.addHandler(fh)
 
    #capture logs from Twisted
    observer = log.PythonLoggingObserver()
    observer.start()

    #check for authfile in config, or on commandline
    try:
        authfile = config['authfile']
    except KeyError:
        if (args.authfile == None):
            ThrowCritical("No authorization / rules file specified. Specify one in your config, or use -a")
        else:
            authfile = args.authfile

    #load the authorization file (ACLs)
    users = load_authfile(authfile)

    debug.debug("Found %s users" % len(users), extra={'clientip':'-', 'user':'-'})

    if (config['plaintext-support'] == False and config['ssl-support'] == False):
        ThrowCritical("You must enable plaintext support or SSL support.")

    # Check for SSL support
    if (config['ssl-support'] == True):
        if os.path.exists(config['ssl-key-file']):
            if (os.path.exists(config['ssl-cert-file'])):
                ssl_factory = Factory()
                ssl_factory.protocol = Redis2
                reactor.listenSSL(config['ssl-port'], RedisFactory(), ssl.DefaultOpenSSLContextFactory(config['ssl-key-file'], config['ssl-cert-file']))
            else:
                ThrowCritical("The SSL certificate file specified in the config does not exist")
        else:
            ThrowCritical("The SSL key file specified in the config does not exist")

    # Open an IPv4 TCP endpoint on 6370
    if (config['plaintext-support'] == True):
        endpoint = TCP4ServerEndpoint(reactor, config['plaintext-port'])
        endpoint.noisy = False
        endpoint.listen(RedisFactory())
        reactor.run()


#################
#	Entrypoint  #
#################

if __name__ == "__main__":
    sys.path.insert(0,'modules/')
    main()

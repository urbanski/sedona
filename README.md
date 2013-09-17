#Sedona

[![Build Status](https://travis-ci.org/urbanski/sedona.png?branch=master)](https://travis-ci.org/urbanski/sedona)

Sedona is an application firewall for [Redis](http://redis.io). Sedona augments Redis installations by adding support for *authentication*, *authorization* and *encryption*.

The goals of the Sedona project are to:

* Enhance the security of Redis installations by supporting encryption, authentication, and authorization for Redis deployments.
* Ensure backwards compatbility with the existing Redis 2.0 protocol and client libraries.

###Why does Redis need an application firewall?
Redis is designed to provide scalable, reliable, high-performance storage services to trusted clients. The [Redis security model](http://redis.io/topics/security) states that "Redis is designed to be accessed by trusted clients inside trusted environments." Traditional security features like authentication, authorization and encryption are unimplemented in the Redis core with a few notable exceptions.

There are instances where it would be beneficial for a remote client to be able to securely access a Redis installation or have limited access to specific commands within an installation. Sedona provides this functionality in the form of an application firewall. With Sedona, traditional, trusted Redis clients can continue to directly access the Redis server. However, if a client is untrusted or requires limited access to an installation then Sedona can limit the authorization of that client to the server.

## [Ready to get started? Install Sedona](https://github.com/urbanski/sedona/blob/master/INSTALL.md)

##Features

###Authentication
Redis natively supports an authentication command \([AUTH](http://redis.io/commands/auth)\) that allows remote users to authenticate with a server. This command does not support a username and password and does not differentiate between users (a single password is supported for the entire server). Sedona improves upon the [AUTH](http://redis.io/commands/auth) command by supporting distinct accounts (username and password combinations) that are in turn tied to account-specific access control lists (ACLs). These ACLs are used to authorize specific actions within the Redis installation.

Sedona provides this functionality by overriding the AUTH command. This functionality can be disabled if you prefer to use the Redis server for authentication, however, all connections will have the default ACL applied to them.

###Authorization
Sedona can authorize clients using role-based access control lists. These lists are applied on a per-user basis and can be used to explicitly authorize specific types of commands. Authorization is done on a per-command and per-key basis. Individual commands can be authorized or rejected, additionally, access to specific keys from specific commands can be applied for more granular authorization controls.

##Encryption
I am currently working to add SSL support to Sedona. A Redis CLI with SSL support, sedona-cli, will be included in the distribution.

## Project Status

This project is a work in progress! Please help contribute by testing Sedona in your environment, or sending us a pull request!

## System Requirements

* [python](http://www.python.org) (tested on version 2.7)
* [python-twisted](https://pypi.python.org/pypi/Twisted)
* [python-bcrypt](http://www.mindrot.org/projects/py-bcrypt/)
* [pyOpenSSL](https://pypi.python.org/pypi/pyOpenSSL)

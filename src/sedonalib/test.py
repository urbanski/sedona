from nose.tools import *
from user import *
from acl import *
from redis import *

###################
# SedonaUser
###################

def test_SedonaUser___init__():
    #test a null user
    test = SedonaUser("test",{})
    assert_is_instance(test, SedonaUser)
    assert_equals(test.username, "test")
    assert_false(test.auth_required)
    assert_equals(test.auth_method, None)

def test_SedonaUser_authorize():
	#ensure a null-request is rejected
	test = SedonaUser("test", {})
	assert_false(test.authorize(None))

	# simple rule checks
	rq_valid = [ RedisRequest("*2\r\n$3\r\nGET\r\n$3\r\ndog\r\n"),
				 RedisRequest("*2\r\n$3\r\nSET\r\n$3\r\ndog\r\n")
				]
	rq_invalid = [ RedisRequest("*1\r\n$4\r\nPING\r\n"),
					RedisRequest("*1\r\n$8\r\nSHUTDOWN\r\n")
				]

	test = None
	test = 	SedonaUser("test", 
			{"rules":
				[
					{"command": "get", "action": "accept"},
					{"command": "set", "action": "accept"},
					{"action": "reject"}
				]
			})

	for rq in rq_valid:
		assert_equals(test.authorize(rq), SedonaACL.ACTION_ACCEPT)

	for rq in rq_invalid:
		assert_equals(test.authorize(rq), SedonaACL.ACTION_REJECT)

def test_SedonaUser_authorize_keychecks():
	#key-based rule checks
	rq_valid = [ RedisRequest("*2\r\n$3\r\nGET\r\n$3\r\ndog-fido\r\n"),
				 RedisRequest("*3\r\n$3\r\nSET\r\n$12\r\ndog-fido-age\r\n$1\r\n7\r\n")
				]
	rq_invalid = [ RedisRequest("*1\r\n$4\r\nPING\r\n"),
					RedisRequest("*1\r\n$8\r\nSHUTDOWN\r\n"),
					RedisRequest("*1\r\n$4\r\nINFO\r\n"),
					RedisRequest("*2\r\n$3\r\nGET\r\n$13\r\ncat-priscilla\r\n"),
					RedisRequest("*2\r\n$3\r\nSET\r\n$10\r\ncat-vulpix\r\n$4\r\naaaa\r\n"),
					RedisRequest("*2\r\n$3\r\nGET\r\n$5\r\nother\r\n")
				]
	usr = SedonaUser("usr", 
			{"rules":
				[
					{"command": "get", "action": "accept", "key": "dog\-.*"},
					{"command": "set", "action": "accept", "key": "dog\-.*"},
					{"action": "reject"}
				]
			})

	for rq in rq_valid:
		assert_equals(usr.authorize(rq), SedonaACL.ACTION_ACCEPT)

	for rq in rq_invalid:
		assert_equals(usr.authorize(rq), SedonaACL.ACTION_REJECT)

def test_SedonaUser_authenticate():
	pass

####################
# SedonaACL
####################

def test_SedonaACL___init__():
	#test that an invalid ACL specification won't create an ACL
	assert_raises(SedonaInvalidACL, SedonaACL, {})
	assert_raises(SedonaInvalidACL, SedonaACL, {'command': 'get'})
	assert_raises(SedonaInvalidACL, SedonaACL, {'key': 'dogs'})

	#test that a valid ACL will create an ACL
	assert_is_instance(SedonaACL({'action':'DROP'}), SedonaACL)
	assert_is_instance(SedonaACL({'action':'DROP', 'command':'get','key':'dog'}), SedonaACL)

def test_SedonaACL_check_acl():
	#test an valid request against an ACL
	rq = RedisRequest("*2\r\n$3\r\nGET\r\n$3\r\ndog\r\n")
	print rq.command
	print rq.args
	
	getacl = SedonaACL({'command':'get', 'action':'accept'})
	assert_true(getacl.check_acl(rq))
	assert_equal(getacl.command, "GET")
	assert_equal(getacl.action, SedonaACL.ACTION_ACCEPT)

	setacl = SedonaACL({'command':'set', 'action':"reject"})
	assert_false(setacl.check_acl(rq))
	assert_equal(setacl.command, 'SET')
	assert_equal(setacl.action, SedonaACL.ACTION_REJECT)

	dogacl = SedonaACL({'command': 'get', 'key': 'dog', 'action':"reject"})
	assert_true(dogacl.check_acl(rq))
	assert_equal(dogacl.command, 'GET')
	assert_equal(dogacl.action, SedonaACL.ACTION_REJECT)
	assert_equal(dogacl.key, 'dog')

	catacl = SedonaACL({'command': 'get', 'key': 'cat', 'action':"reject"})
	assert_false(catacl.check_acl(rq))
	assert_equal(catacl.command, 'GET')
	assert_equal(catacl.action, SedonaACL.ACTION_REJECT)
	assert_equal(catacl.key, 'cat')

# RedisResponse
# RedisStatusRepy
# RedisErrorReply

def test_RedisResponse():
	rr = RedisResponse("Invalid Request")
	assert_equal(rr.response_text, "Invalid Request")
	assert_equal(str(rr), "$15\r\nInvalid Request\r\n")

def test_RedisStatusReply():
	rr = RedisStatusReply("OK")
	assert_equal(rr.response_text, "OK")
	assert_equal(str(rr), "+OK\r\n")

def test_RedisErrorReply():
	rr = RedisErrorReply("OK")
	assert_equal(rr.response_text, "OK")
	assert_equal(str(rr), "-OK\r\n")

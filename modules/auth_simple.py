import logging
from bcrypt import hashpw

def authenticate(*args, **kwargs):

	request = args[0]
	auth_data = args[1]

	password_attempt = request.args[1].encode('utf-8')
	stored_password = auth_data['auth_simple_password'].encode("utf8")

	logging.debug("In auth_simple.authenticate()")

	if hashpw(password_attempt, stored_password) == stored_password:
		return True
	else:
		return False

def load():
	return ["auth_simple_password"]
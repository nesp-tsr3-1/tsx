from flask import request, make_response, g, jsonify, Blueprint, session
from tsx.db import get_session, User
from tsx.api.util import get_user
from sqlalchemy import exc
import os
import json
import re
from collections import namedtuple
from passlib.context import CryptContext

bp = Blueprint('user', __name__)

# For password hashing
pwd_context = CryptContext(schemes=["argon2"])

# Basic field validation framework

Field = namedtuple("Field", "name title validators")

email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
def validate_email(value, field):
	if not re.match(email_regex, value):
		return "Must be a valid email address"

def validate_required(value, field):
	if value is None or value == "":
		return "%s is required" % field.title

def validate_max_chars(length):
	def v(value, field):
		if len(value) > length:
			return "Must contain no more than %s characters" % length
	return v

def validate_min_chars(length):
	def v(value, field):
		if len(value) < length:
			return "Must contain at least %s characters" % length
	return v

def validate_fields(fields, body):
	errors = {}

	for field in fields:
		value = body[field.name].strip()

		for validator in field.validators:
			message = validator(value, field)
			if message:
				errors[field.name] = message
				break
				# errors.append({
				# 	'field': field.name,
				# 	'message': message
				# })

	return errors

# Routes:

@bp.route('/users', methods = ['POST'])
def create_user():
	body = request.json

	fields = [
		Field(name='email', title='Email address', validators=[validate_required, validate_email]),
		Field(name='first_name', title='First name', validators=[validate_required, validate_max_chars(255)]),
		Field(name='last_name', title='Last name', validators=[validate_required, validate_max_chars(255)]),
		Field(name='phone_number', title='Phone number', validators=[validate_max_chars(32)]),
		Field(name='password', title='Password', validators=[validate_required, validate_min_chars(8)])
	]

	errors = validate_fields(fields, body)

	if len(errors):
		return jsonify(errors), 400

	user = User(
		email=body['email'].strip(),
		first_name=body['first_name'].strip(),
		last_name=body['last_name'].strip(),
		phone_number=body['phone_number'].strip(),
		password_hash=pwd_context.hash(body['password'])
	)

	db_session = get_session()
	try:
		db_session.add(user)
		db_session.commit()
	except exc.IntegrityError:
		# User already exists
		pass

	return "OK", 204 # Success

@bp.route('/login', methods = ['POST'])
def login():
	body = request.json

	fields = [
		Field(name='email', title='Email address', validators=[validate_required, validate_email]),
		Field(name='password', title='Password', validators=[validate_required])
	]

	errors = validate_fields(fields, body)

	if len(errors):
		return jsonify(errors), 400

	db_session = get_session()
	user = db_session.query(User).filter(User.email == body['email']).one_or_none()

	if user is not None and pwd_context.verify(body['password'], user.password_hash):
		session['user_id'] = user.id
		return "OK", 200
	else:
		return jsonify({ 'password': "Invalid email address or password" }), 400

@bp.route('/logout', methods = ['POST'])
def logout():
	session.pop('user_id', None)
	return "OK", 200

# @bp.route('/password_reset_request', methods = ['POST'])
# def password_reset_request():
# 	pass
# 	# generate random token
# 	# record token in database
# 	# email reset link

# @bp.route('/password_reset', methods = ['POST'])
# def password_reset():
# 	pass
# 	# verify token
# 	# update user

@bp.route('/is_logged_in', methods = ['GET'])
def is_logged_in():
	return jsonify(get_user() is not None), 200

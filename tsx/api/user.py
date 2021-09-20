from flask import request, make_response, g, jsonify, Blueprint, session
from tsx.db import get_session, User
from tsx.api.util import get_user, get_roles, db_session
from sqlalchemy import exc
import os
import json
from passlib.context import CryptContext
import secrets
from string import Template
from textwrap import dedent
from tsx.api.validation import *
from tsx.api.mail import send_email
from tsx.config import config

bp = Blueprint('user', __name__)

# For password hashing
pwd_context = CryptContext(schemes=["argon2"])

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

	user = db_session.query(User).filter(User.email == body['email']).one_or_none()
	if user:
		if user.password_hash:
			# User already has an ccount
			return jsonify({ 'email': "An account with this email address already exists" }), 400
	else:
		user = User(email=body['email'].strip())

	user.first_name=body['first_name'].strip()
	user.last_name=body['last_name'].strip()
	user.phone_number=body['phone_number'].strip()
	user.password_hash=pwd_context.hash(body['password'])

	try:
		db_session.add(user)
		db_session.flush()
	except exc.IntegrityError:
		# User already exists
		pass

	db_session.execute("""INSERT INTO user_role (user_id, role_id)
		VALUES (:user_id, (SELECT id FROM role WHERE description = 'Custodian'))""",
		{'user_id': user.id})

	db_session.commit()

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

@bp.route('/users/me', methods = ['GET'])
def current_user():
	user = get_user()
	if user is None:
		return "Not found", 404
	else:
		return jsonify(user_to_json(user)), 200

@bp.route('/users/<int:user_id>/role', methods = ['PUT'])
def update_user_role(user_id):
	user = get_user()

	if 'Administrator' not in get_roles(user):
		return "Forbidden", 403

	body = request.json

	try:
		new_role = body['role']
	except KeyError:
		return "Missing role", 400

	db_session.execute("DELETE FROM user_role WHERE user_id = :user_id", { 'user_id': user_id })
	print(new_role)
	print(user_id)
	db_session.execute("INSERT INTO user_role (user_id, role_id) SELECT :user_id, (SELECT id FROM role WHERE description = :role)", { 'user_id': user_id, 'role': new_role })
	db_session.commit()

	return "OK", 200

@bp.route('/users', methods = ['GET'])
def users():
	user = get_user()

	if 'Administrator' not in get_roles(user):
		return "Forbidden", 403

	sql = """SELECT
		user.id,
		user.email,
		user.first_name,
		user.last_name,
		user.phone_number,
		MAX(role.description = 'Administrator') AS is_admin,
		COALESCE(MAX(role.description), 'Custodian') AS role
	FROM user
	LEFT JOIN user_role ON user.id = user_role.user_id
	LEFT JOIN role ON user_role.role_id = role.id
	GROUP BY user.id"""

	rows = db_session.execute(sql)

	return jsonify([dict(row) for row in rows])

def user_to_json(user):
	roles = get_roles(user)
	return {
		'id': user.id,
		'email': user.email,
		'first_name': user.first_name,
		'last_name': user.last_name,
		'phone_number': user.phone_number,
		'is_admin': 'Administrator' in roles,
		'roles': list(roles)
	}

reset_email_body = Template(dedent("""
	Hi $name,

	We have recieved a request to reset your password for the TSX web interface.

	To reset your password, visit $reset_url

	If you did not request a password reset, please disregard this email.
"""))

reset_email_no_account_body = Template(dedent("""
	Hi,

	We recieved a request to reset your password for the TSX web interface (http://tsx.org.au),
	however no account exists for this email address ($email).

	If you wish to create a new account, visit $root_url#/signup

	If you did not request a password reset, please disregard this email.
"""))

@bp.route('/reset_password', methods = ['POST'])
def reset_password():
	body = request.json

	if 'code' in body:
		# User already has a code - actually reset the password
		fields = [
			Field(name='password', title='Password', validators=[validate_required, validate_min_chars(8)])
		]

		errors = validate_fields(fields, body)

		if len(errors):
			return jsonify(errors), 400

		code = body['code'].strip()
		user = db_session.query(User).filter(User.password_reset_code == code).one_or_none()

		if user == None:
			return jsonify({ 'invalid_code': True }), 400
		else:
			user.password_hash = pwd_context.hash(body['password'])
			user.password_reset_code = None
			db_session.commit()
			return "OK", 200

	else:
		# User doesn't have a code - need to send user a reset link
		fields = [
			Field(name='email', title='Email address', validators=[validate_required, validate_email])
		]

		errors = validate_fields(fields, body)

		if len(errors):
			return jsonify(errors), 400

		email = body['email'].strip()

		user = db_session.query(User).filter(User.email == email).one_or_none()
		if user == None:
			email_body = reset_email_no_account_body.substitute(email=email)
		else:
			# Update reset code in database
			user.password_reset_code = secrets.token_urlsafe(16)
			db_session.commit()

			# Send reset email
			root_url = config.get("api", "root_url")
			reset_url = "%s#/reset_password?code=%s" % (root_url, user.password_reset_code)
			email_body = reset_email_body.substitute(name=user.first_name, reset_url=reset_url, root_url=root_url)

		try:
			send_email(email, 'Password reset request', email_body)
			return "OK", 200
		except:
			return jsonify('There was a problem sending the password reset email. Please try again later.'), 500


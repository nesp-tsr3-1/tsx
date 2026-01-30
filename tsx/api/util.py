import csv
from io import StringIO
from flask import make_response, session, current_app, jsonify, request
from tsx.db.connect import Session
from tsx.db import User
from sqlalchemy import orm
from werkzeug.local import LocalProxy
from sqlalchemy import text
from flask_executor import Executor
import pytz
import re

try:
	from greenlet import getcurrent as _get_ident  # type: ignore
except ImportError:
	from threading import get_ident as _get_ident  # type: ignore

log = LocalProxy(lambda: current_app.logger)

executor = None
def get_executor():
	global executor
	if executor == None:
		executor = Executor(current_app)
	return executor

def csv_response(rows, filename="export.csv"):
	"""Generate CSV response from a list of row values"""
	# Unfortunately Flask doesn't let you output response as an IO Stream, so you have
	# buffer the entire response to a string first.
	si = StringIO()
	cw = csv.writer(si)
	cw.writerow(header)
	for row in rows:
		cw.writerow()
	output = make_response(si.getvalue())
	output.headers["Content-Disposition"] = "attachment; filename=%s" % filename
	output.headers["Content-type"] = "text/csv"
	return output


# This should be used by any web app code for accessing the database. The database connection
# will automatically be released at the end of each request (assuming setup_db() has been called
# at startup - see below)
#
# For example:
#    from tsx.api.util import db_session
#
#    db_session.query(Model)
#
#    OR
#
#    db_session.execute(sql)
db_session = orm.scoped_session(Session, scopefunc= _get_ident)

# Simple interface to insert a row into a table based on a python dict
def db_insert(table, row_dict, replace=False):
	keys, values = zip(*row_dict.items())

	for key in [*keys, table]:
		if not key.isidentifier():
			raise ValueError("%s is not a supported identifier" % key)

	cols = ", ".join("`%s`" % key for key in keys)
	placeholders = ", ".join(":%s" % key for key in keys)
	verb = "REPLACE" if replace else "INSERT"
	sql = "%s INTO `%s` (%s) VALUES (%s)" % (verb, table, cols, placeholders)

	result = db_session.execute(text(sql), row_dict)

	return result.lastrowid

def db_update(table, row_dict, id_column):
	keys, values = zip(*row_dict.items())

	for key in [*keys, table, id_column]:
		if not key.isidentifier():
			raise ValueError("%s is not a supported identifier" % key)

	placeholders = ", ".join("`%s` = :%s" % (key, key) for key in keys if key != id_column)
	sql = "UPDATE `%s` SET %s WHERE `%s` = :%s" % (table, placeholders, id_column, id_column)

	db_session.execute(text(sql), row_dict)

def get_user():
	try:
		user_id = session['user_id']
	except KeyError:
		return None
	return db_session.query(User).get(user_id)

def get_roles(user):
	query = db_session.execute(text("""SELECT role.description
		FROM role
		JOIN user_role ON role.id = user_role.role_id
		WHERE user_role.user_id = :user_id
	"""), {
		'user_id': user.id
	})

	return set(role for (role,) in query.fetchall())

# I would have used Flask-SQLAlchemy, but it requires you to make your database model dependent on Flask
# which makes no sense when you want to use the database in other contexts e.g. from a CLI script.
def setup_db(app):
	"""
	Setup SQLAlchemy session to be cleaned up at the end of every request
	"""
	with app.app_context():
		@app.teardown_appcontext
		def shutdown_session(response_or_exc):
			db_session.remove()
			return response_or_exc

# Useful for converting a DB query result into a JSON response
def jsonify_rows(rows):
	return jsonify([dict(row._mapping) for row in rows])

def get_request_args_or_body():
	if request.content_type == 'application/json':
		return request.get_json()
	else:
		return request.args

def server_timezone():
	return pytz.timezone('Australia/Sydney')

def sanitise_file_name_string(s):
	s = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "_", s)
	s = re.sub(r"[-_\s]+", "_", s)
	return s

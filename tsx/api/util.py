import json, csv
import csv
from io import StringIO
from flask import make_response, g, jsonify, _app_ctx_stack, session, current_app
from tsx.db.connect import Session
from tsx.db import User
from sqlalchemy import orm
from werkzeug.local import LocalProxy
import logging

log = LocalProxy(lambda: current_app.logger)

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
db_session = orm.scoped_session(Session, scopefunc=_app_ctx_stack.__ident_func__)

def get_user():
	try:
		user_id = session['user_id']
	except KeyError:
		return None
	return db_session.query(User).get(user_id)

def get_roles(user):
	query = db_session.execute("""SELECT role.description
		FROM role
		JOIN user_role ON role.id = user_role.role_id
		WHERE user_role.user_id = :user_id
	""", {
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

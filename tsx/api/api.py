from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import tsx.api.lpi_data
from tsx.api.util import setup_db
import tsx.config
import uuid
from flask_cors import CORS
from flask_session import Session
from cachelib.file import FileSystemCache
from flask.json.provider import DefaultJSONProvider
import os.path
import logging

import tsx.api.upload
import tsx.api.lpi_data # legacy
import tsx.api.data_import
import tsx.api.misc
import tsx.api.user
import tsx.api.program_manager
import tsx.api.subset
import tsx.api.program
import tsx.api.results
import tsx.api.custodian_feedback

import datetime

app = Flask('tsx')

is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
if is_gunicorn:
	gunicorn_logger = logging.getLogger('gunicorn.error')
	app.logger.handlers = gunicorn_logger.handlers
	app.logger.setLevel(gunicorn_logger.level)

app.config['UPLOAD_DIR'] = tsx.config.data_dir("upload")

# Enable CORS
CORS(app=app, supports_credentials=True)
# CORS(app=app, send_wildcard=True)

# Setup secret key
app.secret_key = tsx.config.get("api", "secret_key") or "not-secret"
app.config['SESSION_TYPE'] = 'cachelib'
app.config['SESSION_SERIALIZATION_FORMAT'] = 'json'
app.config['SESSION_CACHELIB'] = FileSystemCache(threshold=500, cache_dir=tsx.config.data_dir("flask_session"))
Session(app)

setup_db(app)

app.register_blueprint(tsx.api.upload.bp)
app.register_blueprint(tsx.api.lpi_data.bp) # legacy
app.register_blueprint(tsx.api.data_import.bp)
app.register_blueprint(tsx.api.misc.bp)
app.register_blueprint(tsx.api.user.bp)
app.register_blueprint(tsx.api.program_manager.bp)
app.register_blueprint(tsx.api.subset.bp)
app.register_blueprint(tsx.api.program.bp)
app.register_blueprint(tsx.api.results.bp)
app.register_blueprint(tsx.api.custodian_feedback.bp)

class CustomJSONProvider(DefaultJSONProvider):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat() + 'Z'
		if isinstance(obj, (datetime.date, datetime.time)):
			return obj.isoformat()
		elif isinstance(obj, datetime.timedelta):
			return (datetime.datetime.min + obj).time().isoformat()

		return super().default(obj)

app.json = CustomJSONProvider(app)

# @app.before_first_request
# def app_init():
# 	tsx.api.data_import.start_processing_workers()
# 	tsx.api.data_import.process_unprocessed()

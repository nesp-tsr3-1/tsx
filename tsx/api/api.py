from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import tsx.api.lpi_data
from tsx.api.util import setup_db
import tsx.config
import uuid
from flask_cors import CORS
from flask_session import Session
import os.path

import tsx.api.upload
import tsx.api.lpi_data
import tsx.api.data_import
import tsx.api.misc
import tsx.api.user

import json
import datetime
# import tsx.api.auth

app = Flask('tsx')

app.config['UPLOAD_DIR'] = tsx.config.data_dir("upload")

# Enable CORS
CORS(app=app, supports_credentials=True)
# CORS(app=app, send_wildcard=True)

# Setup secret key
app.secret_key = tsx.config.get("api", "secret_key") or "not-secret"
# app.config['SECRET_KEY'] = tsx.config.get("api", "secret_key") or "not-secret"
app.config['SESSION_TYPE']='filesystem'
Session(app)

setup_db(app)

app.register_blueprint(tsx.api.upload.bp)
app.register_blueprint(tsx.api.lpi_data.bp)
app.register_blueprint(tsx.api.data_import.bp)
app.register_blueprint(tsx.api.misc.bp)
app.register_blueprint(tsx.api.user.bp)


class DateTimeEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat() + 'Z'
		if isinstance(obj, (datetime.date, datetime.time)):
			return obj.isoformat()
		elif isinstance(obj, datetime.timedelta):
			return (datetime.datetime.min + obj).time().isoformat()

		return super(DateTimeEncoder, self).default(obj)

app.json_encoder = DateTimeEncoder
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import tsx.api.lpi_data
from tsx.api.util import setup_db
import tsx.config
import uuid
from flask_cors import CORS

import tsx.api.upload
import tsx.api.lpi_data
import tsx.api.data_import
import tsx.api.misc
# import tsx.api.auth

app = Flask('tsx')

app.config['UPLOAD_DIR'] = tsx.config.data_dir("upload")

# Enable CORS
CORS(app=app, supports_credentials=True)

# Setup secret key
app.secret_key = tsx.config.get("api", "secret_key") or "not-secret"

setup_db(app)

app.register_blueprint(tsx.api.upload.bp)
app.register_blueprint(tsx.api.lpi_data.bp)
app.register_blueprint(tsx.api.data_import.bp)
app.register_blueprint(tsx.api.misc.bp)

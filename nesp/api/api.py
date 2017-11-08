from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import nesp.api.lpi_data
from nesp.api.util import setup_db
import nesp.config
import uuid
from flask_cors import CORS

import nesp.api.upload
import nesp.api.lpi_data
import nesp.api.data_import
# import nesp.api.auth

app = Flask('nesp')

app.config['UPLOAD_DIR'] = nesp.config.data_dir("upload")

# Enable CORS
CORS(app=app, supports_credentials=True)

# Setup secret key
app.secret_key = nesp.config.get("api", "secret_key") or "not-secret"

setup_db(app)

app.register_blueprint(nesp.api.upload.bp)
app.register_blueprint(nesp.api.lpi_data.bp)
app.register_blueprint(nesp.api.data_import.bp)

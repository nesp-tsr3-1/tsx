from flask import Blueprint, render_template, session, abort, request, jsonify, current_app, send_file
import json
import os
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint('upload', __name__)

def get_upload_path(upload_uuid, meta=False):
	if meta:
		upload_uuid = upload_uuid + ".json"
	return os.path.join(current_app.config['UPLOAD_DIR'], upload_uuid)

def get_upload_name(upload_uuid):
	with open(get_upload_path(upload_uuid, meta=True)) as meta_file:
		meta = json.load(meta_file)
		return meta['name']


@bp.route('/uploads', methods = ['POST'])
def post_upload():
	"""
	Accept file upload

	A unique ID (UUID) is generated for each uploaded file and this is used as the filename to save the upload to.
	An accompanying <UUID>.json file is also created which contains upload metadata such as the MIME type.
	"""

	result = []
	files = list(request.files.values())

	if len(files) > 0:
		file = files[0]
		# save file
		upload_uuid = str(uuid.uuid4())
		file.save(get_upload_path(upload_uuid))

		# save metadata
		meta = {
			'type': file.mimetype,
			'name': file.filename
		}
		with open(get_upload_path(upload_uuid, meta=True), "w") as meta_file:
			json.dump(meta, meta_file)

		return jsonify({
			'uuid': upload_uuid,
			'filename': file.filename
		})

	else:
		return jsonify("No file detected"), 400

@bp.route('/uploads/<id>', methods = ['GET'])
def get_upload(id=None):
	if id:
		"""Retrieve previously uploaded file"""
		filename = secure_filename(id)

		with open(get_upload_path(filename, meta=True), "r") as meta_file:
			meta = json.load(meta_file)
			type = meta['type']
			download_filename = meta['name']

		response = send_file(get_upload_path(filename))
		response.headers['Content-Type'] = type
		if filename:
			response.headers['Content-Disposition'] = 'attachment; filename="%s"' % download_filename
		return response

from flask import Blueprint, jsonify, request, send_file, session
from tsx.util import next_path, local_iso_datetime
from tsx.api.util import db_session, get_user, get_roles
from tsx.api.upload import get_upload_path, get_upload_name
from tsx.importer import Importer
from tsx.config import data_dir
from tsx.db import User, Source, get_session, DataImport, DataProcessingNotes, t_user_source
import logging
import os
from threading import Thread, Lock
import json
import traceback
from shutil import rmtree
import time
from tsx.api.validation import *

bp = Blueprint('data_import', __name__)

imports_path = data_dir("imports")
running_imports = {} # Holds information about running imports

lock = Lock() # Used to sync data between import thread and main thread

def update_import_statuses_after_restart():
	db_session.execute("""UPDATE data_import
		SET status_id = (SELECT id FROM data_import_status WHERE code = 'checked_error')
		WHERE status_id = (SELECT id FROM data_import_status WHERE code = 'checking')""")

	db_session.execute("""UPDATE data_import
		SET status_id = (SELECT id FROM data_import_status WHERE code = 'import_error')
		WHERE status_id = (SELECT id FROM data_import_status WHERE code = 'importing')""")

	db_session.commit()

update_import_statuses_after_restart()

def permitted(user, action, resource_type, resource_id=None):
	if user == None:
		return False

	user_roles = get_roles(user)
	if 'Administrator' in user_roles:
		return True

	if resource_type == 'source' and 'Custodian' in user_roles:
		if action in ('create', 'list'):
			return True
		if action in ('get', 'update', 'delete'):
			return len(db_session.execute("""SELECT 1 FROM user_source WHERE user_id = :user_id AND source_id = :source_id""", {
				'source_id': resource_id,
				'user_id': user.id
				}).fetchall()) > 0

	if resource_type == 'notes' and 'Custodian' in user_roles:
		try:
			notes = db_session.query(DataProcessingNotes).get(resource_id)
			return notes.user_id == user.id
		except:
			return False

	return False

@bp.route('/data_sources', methods = ['GET'])
def get_sources():
	user = get_user()

	if not permitted(user, 'list', 'source'):
		return "Not authorized", 401

	rows = db_session.execute(
		"""SELECT
			source.id,
			source.description,
			data_import_status.code AS status,
			data_import.time_created
		FROM source
		LEFT JOIN (SELECT source_id, max(data_import.id) AS data_import_id FROM data_import GROUP BY source_id) AS latest_import
			ON latest_import.source_id = source.id
		LEFT JOIN data_import ON latest_import.data_import_id = data_import.id
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		WHERE
			(
				EXISTS (SELECT 1 FROM user_role WHERE user_id = :user_id AND role_id = 1) OR
				(
					EXISTS (SELECT 1 FROM user_role WHERE user_id = :user_id AND role_id = 2) AND
					source.id IN (SELECT source_id FROM user_source WHERE user_id = :user_id)
				)
			)
		""",
		{ 'user_id': user.id })

	return jsonify_rows(rows)

def jsonify_rows(rows):
	return jsonify([dict(row.items()) for row in rows])

@bp.route('/data_sources', methods = ['POST'])
def create_source():
	return create_or_update_source()

@bp.route('/data_sources/<int:source_id>', methods = ['PUT'])
def update_source(source_id = None):
	if source_id == None:
		return "Not found", 404

	return create_or_update_source(source_id)

@bp.route('/data_sources/<int:source_id>', methods = ['GET'])
def get_source(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	return jsonify(source_to_json(source)), 200

@bp.route('/data_sources/<int:source_id>/imports', methods = ['GET'])
def get_source_imports(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	rows = db_session.execute("""SELECT
		data_import.id,
		data_import.filename,
		data_import.data_type,
		data_import_status.code AS status,
		data_import.time_created,
		data_import.upload_uuid
		FROM data_import
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		WHERE data_import.source_id = :source_id
	""", { 'source_id': source_id })

	return jsonify_rows(rows)

# --------- Data processing notes

@bp.route('/data_sources/<int:source_id>/notes', methods = ['GET'])
def get_source_processing_notes(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	rows = db_session.execute("""SELECT
		notes.id,
		user.first_name,
		user.last_name,
		user.email,
		notes.source_id,
		notes.time_created,
		notes.notes,
		user.id = :user_id AS editable
		FROM data_processing_notes notes
		JOIN user ON notes.user_id = user.id
		WHERE notes.source_id = :source_id
	""", { 'source_id': source_id, 'user_id': user.id })

	return jsonify_rows(rows)

@bp.route('/data_sources/<int:source_id>/notes', methods = ['POST'])
def create_source_processing_notes(source_id=None):
	user = get_user()

	if not permitted(user, 'update', 'source', source_id):
		return "Not authorized", 401

	body = request.json

	# TODO: validate json

	notes = DataProcessingNotes()
	notes.notes = body['notes']
	notes.user_id = user.id
	notes.source_id = source_id
	db_session.add(notes)
	db_session.commit()

	return "OK", 201

@bp.route('/data_sources/<int:source_id>/notes/<int:note_id>', methods = ['PUT'])
def update_source_processing_notes(source_id=None, note_id=None):
	user = get_user()

	if not permitted(user, 'update', 'source', source_id):
		return "Not authorized", 401

	notes = db_session.query(DataProcessingNotes).get(note_id)

	if notes.source_id != source_id:
		return "Source id doesn't match", 400

	body = request.json # TODO: validate json
	notes.notes = body['notes']
	db_session.add(notes)
	db_session.commit()

	return "OK", 201

@bp.route('/data_sources/<int:source_id>/notes/<int:note_id>', methods = ['DELETE'])
def delete_source_processing_notes(source_id=None, note_id=None):
	user = get_user()

	if not permitted(user, 'delete', 'source', source_id):
		return "Not authorized", 401

	notes = db_session.query(DataProcessingNotes).get(note_id)

	if notes.source_id != source_id:
		return "Source id doesn't match", 400

	db_session.delete(notes)
	db_session.commit()

	return "OK", 200

# --------- Custodians

@bp.route('/data_sources/<int:source_id>/custodians', methods = ['GET'])
def get_source_custodians(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	rows = db_session.execute("""SELECT
		user.first_name,
		user.last_name,
		user.email,
		user.id
		FROM user_source
		JOIN user ON user_source.user_id = user.id
		WHERE user_source.source_id = :source_id
	""", { 'source_id': source_id })

	return jsonify_rows(rows)

@bp.route('/data_sources/<int:source_id>/custodians', methods = ['POST'])
def create_source_custodian(source_id=None):
	user = get_user()

	if not permitted(user, 'update', 'source', source_id):
		return "Not authorized", 401

	body = request.json

	email = body["email"]

	if not re.match(email_regex, email):
		return jsonify({ 'error' : '"%s" is not a valid email address' % email }), 400

	custodian = db_session.query(User).filter(User.email == email).one_or_none()

	if not custodian:
		error_message = 'No user found with the email address "%s". (Note: custodians must first create an account before they can be added)' % email
		return jsonify({ 'error': error_message }), 400

	rows = db_session.execute("""SELECT 1
		FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id
	""", { 'source_id': source_id, 'user_id': custodian.id })

	if len(list(rows)) == 0:
		db_session.execute("""INSERT INTO user_source (user_id, source_id) VALUES (:user_id, :source_id)""",
			{ 'source_id': source_id, 'user_id': custodian.id })
		db_session.commit()

	return "OK", 201

@bp.route('/data_sources/<int:source_id>/custodians/<int:user_id>', methods = ['DELETE'])
def delete_source_custodian(source_id=None, user_id=None):
	user = get_user()

	if not permitted(user, 'update', 'source', source_id):
		return "Not authorized", 401

	db_session.execute("""DELETE FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id""", { 'source_id': source_id, 'user_id': user_id })
	db_session.commit()

	return "OK", 200

#------


def create_or_update_source(source_id=None):
	action = 'update' if source_id else 'create'

	user = get_user()

	if not permitted(user, action, 'source', source_id):
		return "Not authorized", 401

	if source_id:
		source = db_session.query(Source).get(source_id)
	else:
		source = Source()

	if not source:
		return "Not found", 400

	body = request.json

	errors = validate_fields(source_fields, body)

	if len(errors):
		return jsonify(errors), 400

	update_source_from_json(source, body)
	db_session.add(source)
	db_session.flush()

	db_session.execute("""INSERT INTO user_source (user_id, source_id) VALUES (:user_id, :source_id)""",
			{ 'source_id': source.id, 'user_id': user.id })

	db_session.commit()

	return jsonify(source_to_json(source)), 200 if source_id else 201


def update_source_from_json(source, json):
	def clean(value):
		if type(value) == str:
			value = value.strip()
		return value

	for field in source_fields:
		setattr(source, field.name, clean(json.get(field.name)))

def source_to_json(source):
	json = {
		'id': source.id
	}
	for field in source_fields:
		json[field.name] = getattr(source, field.name)
	return json

source_fields = [
	Field(name='description', title='Dataset description', validators=[validate_required, validate_max_chars(255)]),
	Field(name='provider', title='Dataset provider', validators=[validate_required, validate_max_chars(255)]),
	Field(name='authors', title='Author(s)', validators=[validate_required, validate_max_chars(255)]),

	Field(name='contact_name', title='Full name', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_position', title='Position', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_email', title='Email address', validators=[validate_required, validate_email]),
	Field(name='contact_phone', title='Phone number', validators=[validate_max_chars(32)])
]

@bp.route('/imports', methods = ['POST'])
def post_import():
	user = get_user()

	body = request.json

	try:
		source_id = body['source_id']
	except KeyError:
		return jsonify('source_id is required'), 400

	if not permitted(user, 'update', 'source', source_id):
		return 'Not authorized', 401

	# Check upload parameter
	if 'upload_uuid' not in body:
		return jsonify("upload_uuid is required"), 400

	upload_uuid = body['upload_uuid']
	file_path = get_upload_path(upload_uuid)

	if not os.path.exists(file_path):
		return jsonify("invalid upload_uuid"), 400

	# Create new working directory for the import
	data_import = DataImport(
		source_id = source_id,
    	status_id = 1,
    	upload_uuid = body['upload_uuid'],
    	filename = get_upload_name(upload_uuid),
    	data_type = body.get('data_type'),
    	user_id = user.id
	)
	db_session.add(data_import)
	db_session.commit()
	import_id = data_import.id

	# working_path = os.path.join(imports_path, "%04d" % import_id)

	# working_path, import_id = next_path(os.path.join(imports_path, "%04d"))
	# os.makedirs(working_path)

	process_import_async(import_id, 'checking')

	# TODO - Ideally should return 201 Created and URL of new resource
	return jsonify(data_import_json(load_import(import_id)))


status_ids = { code: status_id for status_id, code in db_session.execute("SELECT id, code FROM data_import_status").fetchall()}
status_codes = {v: k for k, v in status_ids.items()}

def process_import_async(import_id, status):
	info = load_import(import_id)

	file_path = get_upload_path(info.upload_uuid)
	working_path = import_path(import_id)
	os.makedirs(working_path)
	data_type = info.data_type

	with lock:
		running_imports[import_id] = {
			'started': local_iso_datetime(),
			'status': status,
			'total_rows': 0,
			'processed_rows': 0
		}

	def result_callback(result):
		with lock:
			del running_imports[import_id]

		success = result['errors'] == 0

		if status == 'checking':
			new_status = 'checked_ok' if success else 'checked_error'
		elif status == 'importing':
			new_status = 'imported' if success else 'import_error'

		info = load_import(import_id)
		info.status_id = status_ids[new_status]
		info.error_count = result['errors']
		info.warning_count = result['warnings']
		db_session.commit()

	def progress_callback(processed_rows, total_rows):
		with lock:
			running_imports[import_id]['total_rows'] = total_rows
			running_imports[import_id]['processed_rows'] = processed_rows

	# Start import process
	t = Thread(target = process_import, args = (file_path, working_path, data_type, status == 'importing', progress_callback, result_callback, info.source_id))
	t.start()

# This is called off the main thread
# Ideally we would run this in a separate process, but Python 2 multiprocessing is broken/hard. Easy with Python 3 though.
def process_import(file_path, working_path, data_type, commit, progress_callback, result_callback, source_id):
	try:
		# Create logger for this import
		log_file = os.path.join(working_path, 'import.log')
		log = logging.getLogger('%s_%s' % (working_path, time.time()))
		handler = logging.FileHandler(log_file, mode='w')
		handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
		handler.setLevel(logging.INFO)
		log.setLevel(logging.INFO)
		log.addHandler(handler)

		importer = Importer(file_path, commit = commit, data_type = data_type, logger = log, progress_callback = progress_callback, source_id = source_id)
		importer.ingest_data()

		result_callback({
			'warnings': importer.warning_count,
			'errors': importer.error_count
		})
	except:
		traceback.print_exc()
		result_callback({
			'warnings': 0,
			'errors': 1
		})


@bp.route('/imports/<int:import_id>', methods = ['PUT'])
def update_import(import_id=None):
	body = request.json
	data_import = load_import(import_id)

	if not data_import:
		return "Not found", 404

	new_status = body['status']
	old_status = status_codes[data_import.status_id]

	# Make sure this is a valid state transition
	if (old_status, new_status) not in (('checked_ok', 'checking'), ('checked_ok', 'importing'), ('checked_error', 'checking'), ('import_error', 'checking')):
		return "Invalid status change %s -> %s" % (old_status, new_status), 400

	if new_status == 'importing' and data_import.upload_uuid != body['upload_uuid']:
		return "Attempting to import unchecked upload", 400

	data_import.upload_uuid = body['upload_uuid']
	data_import.data_type = body.get('data_type', 1)
	db_session.commit()

	process_import_async(import_id, new_status)

	return jsonify(data_import_json(data_import))

def data_import_json(data_import):
	result = {
		'id': data_import.id,
		'filename': data_import.filename,
		'data_type': data_import.data_type,
		'time_created': data_import.time_created,
		'upload_uuid': data_import.upload_uuid,
		'status': status_codes[data_import.status_id]
	}

	with lock:
		if data_import.id in running_imports:
			result.update(running_imports[data_import.id])

	return result


# @bp.route('/imports/<int:import_id>', methods = ['DELETE'])
# def delete_import(import_id=None):
# 	info = load_import(import_id)

# 	if not info:
# 		return "Not found", 404

# 	db_session.delete(info)
# 	db_session.commit()

# 	return "OK", 200

# @bp.route('/imports', methods = ['GET'])
# def list_imports():
# 	result = [import_info(import_id, include_running = True) for import_id in os.listdir(imports_path)]
# 	return jsonify(result)

@bp.route('/imports/<int:import_id>', methods = ['GET'])
def get_import(import_id=None):
	data_import = load_import(import_id, include_running = True)

	if not data_import:
		return "Not found", 404

	return jsonify(data_import_json(data_import))

@bp.route('/imports/<int:import_id>/log', methods = ['GET'])
def get_import_log(import_id=None):
	return send_file(os.path.join(import_path(import_id), 'import.log'), mimetype = 'text/plain', cache_timeout = 5)

def import_path(id):
	return os.path.join(imports_path, "%04d" % int(id))

def load_import(import_id, include_running = False):
	try:
		return db_session.query(DataImport).get(int(import_id))
	except:
		return None

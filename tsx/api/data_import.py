from flask import Blueprint, jsonify, request, send_file, session, Response
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
from tsx.api.permissions import permitted
from queue import Queue
import subprocess
from tsx.api.util import log
from sqlalchemy import text

bp = Blueprint('data_import', __name__)

imports_path = data_dir("imports")
running_imports = {} # Holds information about running imports

lock = Lock() # Used to sync data between import thread and main thread

def update_import_statuses_after_restart():
	db_session.execute(text("""UPDATE data_import
		SET status_id = (SELECT id FROM data_import_status WHERE code = 'checked_error')
		WHERE status_id = (SELECT id FROM data_import_status WHERE code = 'checking')"""))

	db_session.execute(text("""UPDATE data_import
		SET status_id = (SELECT id FROM data_import_status WHERE code = 'import_error')
		WHERE status_id = (SELECT id FROM data_import_status WHERE code = 'importing')"""))

	db_session.commit()

update_import_statuses_after_restart()

@bp.route('/data_sources', methods = ['GET'])
def get_sources():
	user = get_user()

	if not permitted(user, 'list', 'source'):
		return "Not authorized", 401

	db_session.execute(text("SET time_zone = '+00:00'"))

	program_id = request.args.get('program_id')

	print(user.id)

	rows = db_session.execute(
		text("""SELECT
			source.id,
			source.description,
			data_import_status.code AS status,
			source.time_created
		FROM source
		LEFT JOIN (SELECT source_id, max(data_import.id) AS data_import_id FROM data_import GROUP BY source_id) AS latest_import
			ON latest_import.source_id = source.id
		LEFT JOIN data_import ON latest_import.data_import_id = data_import.id
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		WHERE
			(
				EXISTS (SELECT 1 FROM user_role WHERE user_id = :user_id AND role_id = 1) OR
				(
					EXISTS (SELECT 1 FROM user_role WHERE user_id = :user_id AND role_id IN (2, 3)) AND
					source.id IN (SELECT source_id FROM user_source WHERE user_id = :user_id)
				) OR
				(
					EXISTS (SELECT 1 FROM user_role WHERE user_id = :user_id AND role_id = 3) AND
					source.monitoring_program_id IN (SELECT monitoring_program_id FROM user_program_manager WHERE user_id = :user_id)
				)
			)
		AND (:program_id IS NULL OR monitoring_program_id = :program_id)
		"""),
		{ 'user_id': user.id, 'program_id': program_id })

	return jsonify_rows(rows)

def jsonify_rows(rows):
	return jsonify([dict(row._mapping) for row in rows])

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

	result = source_to_json(source)

	result['can_delete'] = permitted(user, 'delete', 'source', source_id)
	result['can_import_data'] = permitted(user, 'import_data', 'source', source_id)
	result['can_manage_custodians'] = permitted(user, 'manage_custodians', 'source', source_id)

	return jsonify(result), 200


@bp.route('/data_sources/<int:source_id>', methods = ['DELETE'])
def delete_source(source_id=None):
	user = get_user()

	if not permitted(user, 'delete', 'source', source_id):
		return "Not authorized", 401

	db_session.execute(text("""DELETE FROM user_source WHERE source_id = :source_id"""), { 'source_id': source_id })
	db_session.execute(text("""DELETE FROM data_import WHERE source_id = :source_id"""), { 'source_id': source_id })
	db_session.execute(text("""DELETE FROM source WHERE id = :source_id"""), { 'source_id': source_id })
	remove_orphaned_monitoring_programs()
	db_session.commit()

	return "OK", 200

@bp.route('/data_sources/<int:source_id>/imports', methods = ['GET'])
def get_source_imports(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	db_session.execute(text("SET time_zone = '+00:00'"))

	rows = db_session.execute(text("""SELECT
		data_import.id,
		data_import.filename,
		data_import.data_type,
		data_import_status.code AS status,
		data_import.time_created,
		data_import.upload_uuid
		FROM data_import
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		WHERE data_import.source_id = :source_id
	"""), { 'source_id': source_id })

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

	db_session.execute(text("SET time_zone = '+00:00'"))

	rows = db_session.execute(text("""SELECT
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
	"""), { 'source_id': source_id, 'user_id': user.id })

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

	if not permitted(user, 'manage_custodians', 'source', source_id):
		return "Not authorized", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	rows = db_session.execute(text("""SELECT
		user.first_name,
		user.last_name,
		user.email,
		user.id
		FROM user_source
		JOIN user ON user_source.user_id = user.id
		WHERE user_source.source_id = :source_id
	"""), { 'source_id': source_id })

	return jsonify_rows(rows)

auto_create_custodians = True

@bp.route('/data_sources/<int:source_id>/custodians', methods = ['POST'])
def create_source_custodian(source_id=None):
	user = get_user()

	if not permitted(user, 'manage_custodians', 'source', source_id):
		return "Not authorized", 401

	body = request.json

	email = body["email"]

	if not re.match(email_regex, email):
		return jsonify({ 'error' : '"%s" is not a valid email address' % email }), 400

	custodian = db_session.query(User).filter(User.email == email).one_or_none()

	if not custodian:
		if auto_create_custodians:
			custodian = User(email=email)
			db_session.add(custodian)
			db_session.flush()
		else:
			error_message = 'No user found with the email address "%s". (Note: custodians must first create an account before they can be added)' % email
			return jsonify({ 'error': error_message }), 400

	rows = db_session.execute(text("""SELECT 1
		FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id
	"""), { 'source_id': source_id, 'user_id': custodian.id })

	if len(list(rows)) == 0:
		db_session.execute(text("""INSERT INTO user_source (user_id, source_id) VALUES (:user_id, :source_id)"""),
			{ 'source_id': source_id, 'user_id': custodian.id })
		db_session.commit()

	return "OK", 201

@bp.route('/data_sources/<int:source_id>/custodians/<int:user_id>', methods = ['DELETE'])
def delete_source_custodian(source_id=None, user_id=None):
	user = get_user()

	if not permitted(user, 'manage_custodians', 'source', source_id):
		return "Not authorized", 401

	db_session.execute(text("""DELETE FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id"""), { 'source_id': source_id, 'user_id': user_id })
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

	if action == 'create':
		db_session.execute(text("""INSERT INTO user_source (user_id, source_id) VALUES (:user_id, :source_id)"""),
				{ 'source_id': source.id, 'user_id': user.id })

	else:
		remove_orphaned_monitoring_programs()

	db_session.commit()

	return jsonify(source_to_json(source)), 200 if source_id else 201


def update_source_from_json(source, json):
	def clean(value):
		if type(value) == str:
			value = value.strip()
		return value

	for field in source_fields:
		if field.name == 'monitoring_program':
			source.monitoring_program_id = get_monitoring_program_id(json['monitoring_program'])
		else:
			setattr(source, field.name, clean(json.get(field.name)))


def get_monitoring_program_id(description):
	if not description:
		return None

	for (program_id,) in db_session.execute(text("""SELECT id FROM monitoring_program WHERE description = :description"""), { "description": description}):
		return program_id

	return db_session.execute(text("""
		INSERT INTO monitoring_program (description)
		VALUES (:description)"""),
		{ "description": description}).lastrowid



def source_to_json(source):
	(has_t1_data,) = db_session.execute(text("""SELECT EXISTS (SELECT 1 FROM t1_survey WHERE source_id = :source_id)"""), {"source_id": source.id}).fetchone()
	json = {
		'id': source.id,
		'has_t1_data': has_t1_data
	}
	for field in source_fields:
		if field.name == 'monitoring_program' and source.monitoring_program:
			json['monitoring_program'] = source.monitoring_program.description
		else:
			json[field.name] = getattr(source, field.name)
	return json

source_fields = [
	Field(name='description', title='Dataset description', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='provider', title='Dataset provider', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='authors', title='Author(s)', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='monitoring_program', title='Monitoring program', validators=[validate_max_chars(255)]),

	Field(name='contact_name', title='Full name', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_institution', title='Institution', validators=[validate_required, validate_max_chars(255)]),
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


status_ids = { code: status_id for status_id, code in db_session.execute(text("SELECT id, code FROM data_import_status")).fetchall()}
status_codes = {v: k for k, v in status_ids.items()}

def process_import_async(import_id, status):
	info = load_import(import_id)
	user = get_user()

	file_path = get_upload_path(info.upload_uuid)
	working_path = import_path(import_id)
	os.makedirs(working_path, exist_ok=True)
	data_type = info.data_type

	with lock:
		running_imports[import_id] = {
			'started': local_iso_datetime(),
			'status': status,
			'total_rows': 0,
			'processed_rows': 0,
			'is_admin': 'Administrator' in get_roles(user)
		}

	def result_callback(result):
		is_admin = running_imports[import_id]['is_admin']

		with lock:
			del running_imports[import_id]

		success = result['errors'] == 0

		if status == 'checking':
			new_status = 'checked_ok' if success else 'checked_error'
		elif status == 'importing':
			new_status = ('approved' if is_admin else 'imported') if success else 'import_error'

		info = load_import(import_id)
		info.status_id = status_ids[new_status]
		info.error_count = result['errors']
		info.warning_count = result['warnings']
		db_session.commit()

	def progress_callback(processed_rows, total_rows):
		with lock:
			running_imports[import_id]['total_rows'] = total_rows
			running_imports[import_id]['processed_rows'] = processed_rows

	try:
		# Start import process
		t = Thread(target = process_import, args = (file_path, working_path, data_type, status == 'importing', progress_callback, result_callback, info.source_id, import_id))
		t.start()
	except:
		traceback.print_exc()
		result_callback({
			'warnings': 0,
			'errors': 1
		})

# This is called off the main thread
# Ideally we would run this in a separate process, but Python 2 multiprocessing is broken/hard. Easy with Python 3 though.
def process_import(file_path, working_path, data_type, commit, progress_callback, result_callback, source_id, data_import_id):
	try:
		# Create logger for this import
		log_file = os.path.join(working_path, 'import.log')
		log = logging.getLogger('%s_%s' % (working_path, time.time()))
		handler = logging.FileHandler(log_file, mode='w')
		handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
		handler.setLevel(logging.INFO)
		log.setLevel(logging.INFO)
		log.addHandler(handler)

		importer = Importer(file_path, commit = commit, data_type = data_type, logger = log, progress_callback = progress_callback, source_id = source_id, data_import_id = data_import_id)
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
	data_import.filename = get_upload_name(body['upload_uuid'])
	data_import.data_type = body.get('data_type', 1)
	db_session.commit()

	process_import_async(import_id, new_status)

	return jsonify(data_import_json(data_import))

def remove_orphaned_monitoring_programs():
	db_session.execute(text("""DELETE FROM user_program_manager WHERE monitoring_program_id NOT IN (SELECT monitoring_program_id FROM source WHERE monitoring_program_id IS NOT NULL)"""))
	db_session.execute(text("""DELETE FROM monitoring_program WHERE id NOT IN (SELECT monitoring_program_id FROM source WHERE monitoring_program_id IS NOT NULL)"""))

@bp.route('/imports/<int:import_id>/approve', methods = ['POST'])
def approve_import(import_id=None):
	data_import = load_import(import_id)

	if not data_import:
		return "Not found", 404

	old_status = status_codes[data_import.status_id]

	if old_status != 'imported':
		return "Cannot approve import with status '%s'" % old_status, 400

	user = get_user()
	if not permitted(user, 'approve', 'import', import_id):
		return 'Not authorized', 401

	db_session.execute(text("UPDATE data_import SET status_id = :status_id WHERE id = :import_id"), {
		'status_id': status_ids['approved'],
		'import_id': import_id
	})
	db_session.commit()

	data_import.status_id = status_ids['approved']

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

@bp.route('/imports/<int:import_id>', methods = ['GET'])
def get_import(import_id=None):
	data_import = load_import(import_id)

	if not data_import:
		return "Not found", 404

	return jsonify(data_import_json(data_import))

@bp.route('/imports/<int:import_id>/log', methods = ['GET'])
def get_import_log(import_id=None):
	return send_file(os.path.join(import_path(import_id), 'import.log'), mimetype = 'text/plain', cache_timeout = 5)

def import_path(id):
	return os.path.join(imports_path, "%04d" % int(id))

def load_import(import_id):
	try:
		return db_session.query(DataImport).get(int(import_id))
	except:
		return None


# -- The following is now deprecated, and can be removed once the new on-demand processing model is fully tested

def processed_data_dir(source_id, import_id):
	return os.path.join(data_dir("processed_data"), "source-%04d" % int(source_id), "import-%04d" % int(import_id))

processing_info = {}


@bp.route('/data_sources/<int:source_id>/processed_data', methods = ['GET'])
def get_processed_data(source_id=None):
	(import_id,) = db_session.execute(text("SELECT MAX(id) FROM data_import WHERE source_id = :source_id"), { 'source_id': source_id }).fetchone()

	if import_id == None:
		return "Not found", 404

	with lock:
		pinfo = processing_info.get(import_id)

	if pinfo is None:
		# Maybe processing has completed?
		path = processed_data_dir(source_id, import_id)
		if os.path.exists(path):
			items = []
			agg_path = os.path.join(path, 'aggregated.csv')
			if os.path.exists(agg_path):
				items.append({ 'name': 'Aggregated time series (CSV format)', 'id': 'aggregated.csv' })
			trend_path = os.path.join(path, 'trend.csv')
			if os.path.exists(trend_path):
				items.append({ 'name': 'Population trend (CSV format)', 'id': 'trend.csv' })
			return jsonify({
				'processing_status': 'ready',
				'items': items
			})
		else:
			process_data(source_id, import_id)
			return({ 'processing_status': 'pending' })
	else:
		return jsonify(pinfo)

@bp.route('/data_sources/<int:source_id>/processed_data/<item_id>', methods = ['GET'])
def get_processed_data_item(source_id=None, item_id=None):
	(import_id,) = db_session.execute(text("SELECT MAX(id) FROM data_import WHERE source_id = :source_id"), { 'source_id': source_id }).fetchone()

	if import_id == None:
		return "Not found", 404

	path = processed_data_dir(source_id, import_id)
	item_path = os.path.join(path, item_id)

	return send_file(item_path, mimetype = 'text/csv', cache_timeout = 5)

work_q = Queue()

def process_data(source_id, import_id):
	with lock:
		pinfo = processing_info.get(import_id)

		if pinfo is None:
			processing_info[import_id] = { 'processing_status': 'processing' }
		else:
			return

	work_q.put((source_id, import_id))


processing_workers_started = False
def start_processing_workers():
	return
	if processing_workers_started:
		return
	processing_manager_started = True
	for i in range(0, 4):
		t = Thread(target = process_worker)
		t.start()

def process_worker():
	while True:
		source_id, import_id = work_q.get()
		output_dir = processed_data_dir(source_id, import_id)
		if not os.path.exists(output_dir):
			subprocess.run(['python3', '-m', 'tsx.process', 'single_source', str(source_id), '-o', output_dir])
		else:
			print("Already processed: %s" % import_id)
		with lock:
			del processing_info[import_id]

def process_unprocessed():
	for (source_id,import_id) in db_session.execute(text("SELECT source_id, max(id) FROM data_import WHERE source_id IS NOT NULL GROUP BY source_id")):
		process_data(source_id, import_id)

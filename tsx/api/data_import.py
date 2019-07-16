from flask import Blueprint, jsonify, request, send_file, session
from tsx.util import next_path, local_iso_datetime
from tsx.api.util import db_session, get_user
from tsx.api.upload import get_upload_path, get_upload_name
from tsx.importer import Importer
from tsx.config import data_dir
from tsx.db import User
import logging
import os
from threading import Thread, Lock
import json
import traceback
from shutil import rmtree
import time

bp = Blueprint('data_import', __name__)

imports_path = data_dir("imports")
running_imports = {} # Holds information about running imports

lock = Lock() # Used to sync data between import thread and main thread

def roles(user):
	query = db.execute("""SELECT role.description
		FROM role
		JOIN user_role ON role.id = user_role.role_id
		WHERE user_role.user_id = :user_id
	""", {
		'user_id': user.id
	})

	return set(role for (role,) in query.fetchall())

def is_admin(user):
	return 'Administrator' in roles(user)

@bp.route('/import/sources', methods = ['GET'])
def get_sources():
	user = get_user()

	if user == None:
		return "Not authorized", 401

@bp.route('/imports', methods = ['POST'])
def post_import():
	user = get_user()

	if user == None or not is_admin(user):
		return "Not authorized", 401

	body = request.json

	# Check upload parameter
	if 'upload_uuid' not in body:
		return jsonify("upload_uuid is required"), 400

	upload_uuid = body['upload_uuid']
	file_path = get_upload_path(upload_uuid)

	if not os.path.exists(file_path):
		return jsonify("invalid upload_uuid"), 400

	if 'name' not in body:
		return jsonify("name is required"), 400
	name = body['name']

	# Create new working directory for the import
	working_path, import_id = next_path(os.path.join(imports_path, "%04d"))
	os.makedirs(working_path)

	save_import_info(import_id, {
		'id': import_id,
		'upload_uuid': body['upload_uuid'],
		'data_type': body.get('data_type'),
		'status': 'init',
		'filename': get_upload_name(upload_uuid),
		'name': name,
		'created': local_iso_datetime()
	})

	process_import_async(import_id, 'checking')

	# TODO - Ideally should return 201 Created and URL of new resource
	return jsonify(import_info(import_id))

def process_import_async(import_id, status):
	info = import_info(import_id)

	file_path = get_upload_path(info['upload_uuid'])
	working_path = import_path(import_id)
	data_type = int(info.get('data_type', 1))

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

		update_import_info(import_id, {
			'status': new_status,
			'errors': result['errors'],
			'warnings': result['warnings']
		})

	def progress_callback(processed_rows, total_rows):
		with lock:
			running_imports[import_id]['total_rows'] = total_rows
			running_imports[import_id]['processed_rows'] = processed_rows

	# Start import process
	t = Thread(target = process_import, args = (file_path, working_path, data_type, status == 'importing', progress_callback, result_callback))
	t.start()

# This is called off the main thread
# Ideally we would run this in a separate process, but Python 2 multiprocessing is broken/hard. Easy with Python 3 though.
def process_import(file_path, working_path, data_type, commit, progress_callback, result_callback):
	try:
		# Create logger for this import
		log_file = os.path.join(working_path, 'import.log')
		log = logging.getLogger('%s_%s' % (working_path, time.time()))
		handler = logging.FileHandler(log_file, mode='w')
		handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
		handler.setLevel(logging.INFO)
		log.setLevel(logging.INFO)
		log.addHandler(handler)

		importer = Importer(file_path, commit = commit, data_type = data_type, logger = log, progress_callback = progress_callback)
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


@bp.route('/imports/<int:id>', methods = ['PUT'])
def update_import(id=None):
	new_info = request.json
	info = import_info(id)

	if not info:
		return "Not found", 404

	new_status = new_info['status']
	old_status = info['status']

	# Make sure this is a valid state transition
	if (old_status, new_status) not in (('checked_ok', 'checking'), ('checked_ok', 'importing'), ('checked_error', 'checking'), ('import_error', 'checking')):
		return "Invalid status change %s -> %s" % (old_status, new_status), 400

	if new_status == 'importing' and info['upload_uuid'] != new_info['upload_uuid']:
		return "Attempting to import unchecked upload", 400

	update_import_info(id, {
		'upload_uuid': new_info['upload_uuid'],
		'data_type': new_info.get('data_type', 1),
		'name': new_info['name']
	})

	process_import_async(id, new_status)

	return jsonify(import_info(id))

@bp.route('/imports/<int:id>', methods = ['DELETE'])
def delete_import(id=None):
	info = import_info(id)

	if not info:
		return "Not found", 404

	rmtree(import_path(id))

	return "OK", 200

@bp.route('/imports', methods = ['GET'])
def list_imports():
	result = [import_info(import_id, include_running = True) for import_id in os.listdir(imports_path)]
	return jsonify(result)

@bp.route('/imports/<int:id>', methods = ['GET'])
def get_import(id=None):
	info = import_info(id, include_running = True)

	if not info:
		return "Not found", 404

	return jsonify(info)

@bp.route('/imports/<int:id>/log', methods = ['GET'])
def get_import_log(id=None):
	return send_file(os.path.join(import_path(id), 'import.log'), mimetype = 'text/plain', cache_timeout = 5)

def import_path(id):
	return os.path.join(imports_path, "%04d" % int(id))

def import_info_path(id):
	return os.path.join(import_path(id), 'status.json')

def save_import_info(import_id, info):
	import_id = int(import_id)
	with open(import_info_path(import_id), 'w') as file:
		json.dump(info, file)

def update_import_info(import_id, new_info):
	info = import_info(import_id)
	info.update(new_info)
	save_import_info(import_id, info)

def import_info(import_id, include_running = False):
	try:
		import_id = int(import_id)
		with open(import_info_path(import_id), 'r') as file:
			info = json.load(file)

		if info and include_running:
			with lock:
				if import_id in running_imports:
					extra = running_imports[import_id]
					info.update(extra)

		return info

	except:
		return None

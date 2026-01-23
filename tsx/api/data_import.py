from flask import Blueprint, jsonify, request, send_file, session, Response
from tsx.util import next_path, local_iso_datetime, Bunch
from tsx.api.util import db_session, get_user, get_roles, get_executor
from tsx.api.upload import get_upload_path, get_upload_name
from tsx.importer import Importer
from tsx.config import data_dir
from tsx.db import User, Source, get_session, DataImport, DataProcessingNotes, t_user_source, AuditLogItem
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
from string import Template
from textwrap import dedent
from tsx.api.mail import send_admin_notification
from tsx.config import config
from tsx.api.custodian_feedback_shared import update_all_dataset_stats
from tsx.api.custodian_feedback_pdf import generate_archive_pdfs

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
		return "Not authorised", 401

	program_id = request.args.get('program_id')

	rows = db_session.execute(
		text("""SELECT
			JSON_ARRAYAGG(JSON_OBJECT(
				'id', source.id,
				'description', source.description,
				'status', data_import_status.code,
				'time_created', DATE_FORMAT(source.time_created, "%Y-%m-%d %H:%i:%sZ"),
				'last_modified', DATE_FORMAT(
					GREATEST(source.last_modified, COALESCE(data_import.last_modified, source.last_modified)),
					"%Y-%m-%d %H:%i:%sZ"),
				'custodians', (
					SELECT JSON_ARRAYAGG(
						CONCAT(
							COALESCE(CONCAT(user.first_name, " ", user.last_name, " "), ""),
							COALESCE(CONCAT("<", user.email, ">"), "")
						)
					)
					FROM user_source, user
					WHERE user_source.source_id = source.id
					AND user.id = user_source.user_id
					AND user.email IS NOT NULL
				),
				'data_agreement_status_description', data_agreement_status.description,
				'data_agreement_status', data_agreement_status.code,
				'authors', source.authors,
				'provider', source.provider,
				'details', source.details,
				'monitoring_program', monitoring_program.description,
				'data_agreement_files', (
					SELECT JSON_ARRAYAGG(data_agreement_file.filename)
					FROM source_data_agreement
					JOIN data_agreement_file ON data_agreement_file.data_agreement_id = source_data_agreement.data_agreement_id
					WHERE source_data_agreement.source_id = source.id
				)
			))
		FROM source
		LEFT JOIN monitoring_program ON monitoring_program.id = source.monitoring_program_id
		LEFT JOIN (SELECT source_id, max(data_import.id) AS data_import_id FROM data_import GROUP BY source_id) AS latest_import
			ON latest_import.source_id = source.id
		LEFT JOIN data_import ON latest_import.data_import_id = data_import.id
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		JOIN data_agreement_status ON data_agreement_status.id = source.data_agreement_status_id
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

	[(result,)] = rows
	return Response(result, mimetype='application/json')

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
		return "Not authorised", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	result = source_to_json(source)

	result['can_delete'] = permitted(user, 'delete', 'source', source_id)
	result['can_import_data'] = permitted(user, 'import_data', 'source', source_id)
	result['can_manage_custodians'] = permitted(user, 'manage_custodians', 'source', source_id)
	result['can_view_history'] = permitted(user, 'view_history', 'source', source_id)

	is_admin = 'Administrator' in get_roles(user)
	result['show_no_agreement_message'] = is_admin and source.data_agreement_status.code == 'no_agreement'

	return jsonify(result), 200


@bp.route('/data_sources/<int:source_id>', methods = ['DELETE'])
def delete_source(source_id=None):
	user = get_user()

	if not permitted(user, 'delete', 'source', source_id):
		return "Not authorised", 401

	db_session.execute(text("""CALL delete_source(:source_id)"""), { 'source_id': source_id })
	remove_orphaned_monitoring_programs()
	db_session.execute(text("CALL update_custodian_feedback()"))
	db_session.commit()

	return "OK", 200

@bp.route('/data_sources/<int:source_id>/imports', methods = ['GET'])
def get_source_imports(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorised", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

	show_hidden = permitted(user, 'view_hidden_import', 'source', source_id)

	rows = db_session.execute(text("""SELECT
		data_import.id,
		data_import.filename,
		data_import.data_type,
		data_import_status.code AS status,
		data_import.time_created,
		data_import.upload_uuid,
		CASE
			WHEN data_import.is_admin AND :show_hidden
			THEN CONCAT('an administrator (', COALESCE(CONCAT(user.first_name, " ", user.last_name), user.email, 'Unknown user'), ')')
			WHEN data_import.is_admin
			THEN 'an administrator'
			ELSE COALESCE(CONCAT(user.first_name, " ", user.last_name), user.email, 'an unknown user')
		END AS user,
		data_import.is_hidden
		FROM data_import
		LEFT JOIN data_import_status ON data_import_status.id = data_import.status_id
		LEFT JOIN user ON user.id = data_import.user_id
		WHERE data_import.source_id = :source_id
		AND (:show_hidden OR (NOT data_import.is_hidden))
		ORDER BY data_import.time_created DESC
	"""), { 'source_id': source_id, 'show_hidden': show_hidden })

	return jsonify_rows(rows)

# --------- Data processing notes

@bp.route('/data_sources/<int:source_id>/notes', methods = ['GET'])
def get_source_processing_notes(source_id=None):
	user = get_user()

	if not permitted(user, 'get', 'source', source_id):
		return "Not authorised", 401

	source = db_session.query(Source).get(source_id) if source_id else None

	if source == None:
		return "Not found", 404

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
		return "Not authorised", 401

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
		return "Not authorised", 401

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
		return "Not authorised", 401

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
		return "Not authorised", 401

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
		return "Not authorised", 401

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
		return "Not authorised", 401

	db_session.execute(text("""DELETE FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id"""), { 'source_id': source_id, 'user_id': user_id })
	db_session.commit()

	return "OK", 200

#------

@bp.route('/data_sources/<int:source_id>/site_summary')
def site_summary(source_id=None):
	sql = """
		WITH t AS (
			SELECT
				taxon.id AS taxon_id,
				taxon.common_name,
				taxon.scientific_name,
				t1_site.name AS site_name,
				search_type.description AS search_type,
				min(start_date_y) as min_year,
				max(start_date_y) as max_year
			FROM
				t1_survey,
				t1_sighting,
				t1_site,
				search_type,
				taxon
			WHERE t1_survey.id = t1_sighting.survey_id
			AND t1_site.id = t1_survey.site_id
			AND t1_survey.source_id = :source_id
			AND t1_site.search_type_id = search_type.id
			AND taxon.id = t1_sighting.taxon_id
			GROUP BY taxon.id, t1_site.id, search_type.id
		),
		u AS (
			SELECT JSON_OBJECT(
				'taxon_id', taxon_id,
				'common_name', common_name,
				'scientific_name', scientific_name,
				'ts', JSON_ARRAYAGG(
					JSON_OBJECT(
						'site_name', site_name,
						'search_type', search_type,
						'max_year', max_year,
						'min_year', min_year
					)
				)
			) AS item
			FROM t
			GROUP BY taxon_id, common_name, scientific_name
		)
		SELECT JSON_ARRAYAGG(item) FROM u;
	"""

	[(result,)] = db_session.execute(text(sql), { 'source_id': source_id })
	return Response(result or "[]", mimetype='application/json')

@bp.route('/data_sources/<int:source_id>/history', methods = ['GET'])
def get_source_history(source_id=None):
	user = get_user()

	if not permitted(user, 'view_history', 'source', source_id):
		return "Not authorised", 401

	sql = """
	SELECT
		JSON_ARRAYAGG(JSON_OBJECT(
			'id', audit_log_item.id,
			'user', JSON_OBJECT(
				'first_name', user.first_name,
				'last_name', user.last_name,
				'id', user.id
			),
			'action_name', audit_log_item.action_name,
			'data', audit_log_item.resource_data,
			'user_agent', audit_log_item.user_agent,
			'time_recorded', DATE_FORMAT(audit_log_item.time_recorded, "%Y-%m-%d %H:%i:%sZ")
		))
	FROM audit_log_item
	LEFT JOIN user ON user.id = audit_log_item.user_id
	WHERE resource_id = :source_id
	AND action_name IN ('CREATE_SOURCE', 'UPDATE_SOURCE')
	"""

	[(result,)] = db_session.execute(text(sql), { 'source_id': source_id })
	return Response(result or "[]", mimetype='application/json')

def create_or_update_source(source_id=None):
	action = 'update' if source_id else 'create'

	user = get_user()

	if not permitted(user, action, 'source', source_id):
		return "Not authorised", 401

	if source_id:
		source = db_session.query(Source).get(source_id)
		old_source_json = source_to_json(source)
	else:
		source = Source()
		old_source_json = {}

	if not source:
		return "Not found", 400

	body = request.json

	is_admin = 'Administrator' in get_roles(user)
	update_data_agreements = is_admin

	if update_data_agreements:
		# We need to make sure data agreement is only set if status = agreement_executed
		if 'data_agreement_status' in body and body['data_agreement_status'] != 'agreement_executed':
			body['data_agreement_ids'] = []
	else:
		# Strip data agreement fields
		for key in ['data_agreement_status', 'data_agreement_ids']:
			if key in body:
				del body[key]

	context = Bunch()
	context.body = body
	errors = validate_fields(source_fields, body, context)

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

	if update_data_agreements:
		db_session.execute(text("""DELETE FROM source_data_agreement WHERE source_id = :source_id"""), { 'source_id': source.id })
		for data_agreement_id in body.get('data_agreement_ids', []):
			db_session.execute(text("""INSERT INTO source_data_agreement(source_id, data_agreement_id) VALUES (:source_id, :data_agreement_id)"""), { 'source_id': source.id, 'data_agreement_id': data_agreement_id })

	db_session.refresh(source)
	new_source_json = source_to_json(source)

	audit_log_item = source_audit_log_item(old_source_json, new_source_json, action)
	db_session.add(audit_log_item)

	db_session.commit()

	if action == 'create':
		send_admin_notification('New dataset created', new_source_notification_body.substitute(
			source_name=source.description,
			source_url=source_url(source.id),
			first_name=user.first_name,
			last_name=user.last_name,
			email=user.email
		))

	return jsonify(new_source_json), 200 if source_id else 201

def source_audit_log_item(old_json, new_json, action):
	item = AuditLogItem()
	item.user_id = get_user().id
	item.user_agent = request.headers.get('User-Agent')
	item.action_name = action.upper() + "_SOURCE"
	item.resource_id = new_json.get('id')

	field_data = []
	for field in source_fields:
		if field.name not in new_json:
			continue
		elif field.name == 'data_agreement_status':
			old_value = old_json.get('data_agreement_status_description')
			new_value = new_json.get('data_agreement_status_description')
		elif field.name == 'data_agreement_ids':
			old_value = ", ".join(f['filename'] for f in old_json.get('data_agreement_files', [])) or None
			new_value = ", ".join(f['filename'] for f in new_json.get('data_agreement_files', [])) or None
		else:
			old_value = old_json.get(field.name)
			new_value = new_json.get(field.name)
		field_data.append({
			"name": field.name,
			"label": field.title,
			"old_value": old_value,
			"new_value": new_value
		})

	item.resource_data = {
		"fields": field_data
	}
	return item

new_source_notification_body = Template(dedent("""
	A new dataset was created on the TSX data interface.

	Dataset name: $source_name
	Dataset URL: $source_url

	Created by: $first_name $last_name <$email>
"""))

data_import_notification_body = Template(dedent("""
	A new data file was imported using the TSX data interface.

	Dataset name: $source_name
	Dataset URL: $source_url

	Imported by: $first_name $last_name <$email>
"""))


def source_url(source_id):
	root_url = config.get("api", "data_root_url").rstrip("/")
	return "%s/datasets/%s" % (root_url, source_id)

def update_source_from_json(source, json):
	def clean(value):
		if type(value) == str:
			value = value.strip()
		return value

	for field in source_fields:
		if field.name not in json:
			continue
		if field.name == 'monitoring_program':
			source.monitoring_program_id = get_monitoring_program_id(json['monitoring_program'])
		elif field.name == 'source_type':
			source.source_type_id = get_source_type_id(json['source_type'])
		elif field.name == 'data_agreement_status':
			source.data_agreement_status_id = get_data_agreement_status_id(json['data_agreement_status'])
		elif field.name == 'data_agreement_ids':
			pass # These are handled separately
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

def get_source_type_id(description):
	if not description:
		return None

	for (source_type_id,) in db_session.execute(text("""SELECT id FROM source_type WHERE description = :description"""), { "description": description}):
		return source_type_id

	raise ValueError('Invalid source type: %s' % description)

def get_data_agreement_status_id(code):
	if not code:
		return None

	for (status_id,) in db_session.execute(text("""SELECT id FROM data_agreement_status WHERE code = :code"""), { "code": code }):
		return status_id

	raise ValueError('Invalid data agreement status: %s' % code)


def source_to_json(source):
	(has_t1_data,) = db_session.execute(text("""SELECT EXISTS (SELECT 1 FROM t1_survey WHERE source_id = :source_id)"""), {"source_id": source.id}).fetchone()
	json = {
		'id': source.id,
		'has_t1_data': has_t1_data
	}
	for field in source_fields:
		if field.name == 'monitoring_program' and source.monitoring_program:
			json['monitoring_program'] = source.monitoring_program.description
		elif field.name == 'source_type':
			if source.source_type:
				json['source_type'] = source.source_type.description
		elif field.name == 'data_agreement_status':
			json['data_agreement_status'] = source.data_agreement_status.code
		elif field.name == 'data_agreement_ids':
			json['data_agreement_ids'] = get_data_agreement_ids(source.id)
		else:
			json[field.name] = getattr(source, field.name)
	json['data_agreement_status_description'] = source.data_agreement_status.description
	json['data_agreement_status_long_description'] = source.data_agreement_status.long_description

	json['data_agreement_files'] = []
	for (filename, upload_uuid) in get_data_agreement_files(source.id):
		json['data_agreement_files'].append({
			'filename': filename,
			'upload_uuid': upload_uuid
		})

	return json

def get_data_agreement_ids(source_id):
	return [x for (x,) in db_session.execute(text("""
		SELECT data_agreement_id
		FROM source_data_agreement
		WHERE source_data_agreement.source_id = :source_id
	"""), {"source_id": source_id}).fetchall()]

def get_data_agreement_files(source_id):
	return db_session.execute(text("""
		SELECT data_agreement_file.filename, data_agreement_file.upload_uuid
		FROM data_agreement_file, source_data_agreement
		WHERE source_data_agreement.source_id = :source_id
		AND data_agreement_file.data_agreement_id = source_data_agreement.data_agreement_id
	"""), {"source_id": source_id}).fetchall()

def validate_agreement_ids(value, field, context):
	if context.body.get('data_agreement_status') == 'agreement_executed':
		if (not value) or len(value) == 0:
			return "A data agreement is required"
	else:
		if value and len(value) > 0:
			return "Should be empty when no agreement has been executed"

source_fields = [
	Field(name='description', title='Dataset description', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='details', title='Dataset details', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='provider', title='Dataset provider', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='authors', title='Author(s)', validators=[validate_required, validate_max_chars(4096)]),
	Field(name='monitoring_program', title='Monitoring program', validators=[validate_max_chars(255)]),
	Field(name='source_type', title='Source type', validators=[validate_required, validate_one_of('paper/report', 'custodian')]),

	Field(name='contact_name', title='Full name', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_institution', title='Institution', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_position', title='Position', validators=[validate_required, validate_max_chars(255)]),
	Field(name='contact_email', title='Email address', validators=[validate_required, validate_email]),
	Field(name='contact_phone', title='Phone number', validators=[validate_max_chars(32)]),

	Field(name='data_agreement_status', title='Data sharing agreement status', validators=[]),
	Field(name='data_agreement_ids', title='Data sharing agreement', validators=[validate_agreement_ids])
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
		user_id = user.id,
		is_admin = 'Administrator' in get_roles(user)
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

		with lock:
			del running_imports[import_id]

		if new_status in ('imported', 'approved'):
			source = info.source
			send_admin_notification('New data uploaded', data_import_notification_body.substitute(
				source_name=source.description,
				source_url=source_url(source.id),
				first_name=user.first_name,
				last_name=user.last_name,
				email=user.email
			))

		if new_status == 'approved':
			update_latest_approved_data_import(import_id)
			db_session.execute(text("CALL update_custodian_feedback()"))
			db_session.commit()
			update_all_dataset_stats()
			generate_archive_pdfs(info.source_id)

	def progress_callback(processed_rows, total_rows):
		with lock:
			running_imports[import_id]['total_rows'] = total_rows
			running_imports[import_id]['processed_rows'] = processed_rows

	try:
		# Start import process
		# t = Thread(target = process_import, args = (file_path, working_path, data_type, status == 'importing', progress_callback, result_callback, info.source_id, import_id))
		# t.start()
		get_executor().submit(process_import, file_path, working_path, data_type, status == 'importing', progress_callback, result_callback, info.source_id, import_id)
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

@bp.route('/imports/<int:import_id>/show', methods = ['POST'])
def show_import(import_id=None):
	return update_import_visibility(import_id, True)

@bp.route('/imports/<int:import_id>/hide', methods = ['POST'])
def hide_import(import_id=None):
	return update_import_visibility(import_id, False)

def update_import_visibility(import_id, visible):
	user = get_user()

	if not permitted(user, 'update_visbility', 'import', import_id):
		return "Forbidden", 403

	db_session.execute(
		text("UPDATE data_import SET is_hidden = :is_hidden WHERE id = :id"),
		{
			"is_hidden": not visible,
			"id": import_id
		})
	db_session.commit()

	return "OK", 200

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
	update_latest_approved_data_import(import_id)
	db_session.execute(text("CALL update_custodian_feedback()"))
	db_session.commit()
	get_executor().submit(update_all_dataset_stats)
	get_executor().submit(generate_archive_pdfs, data_import.source_id)

	data_import.status_id = status_ids['approved']

	return jsonify(data_import_json(data_import))

def update_latest_approved_data_import(import_id):
	db_session.execute(text("""
		REPLACE INTO source_latest_approved_import (source_id, data_import_id)
		SELECT data_import.source_id, data_import.id
		FROM data_import
		WHERE data_import.id = :import_id
	"""), { 'import_id': import_id })


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
	return send_file(os.path.join(import_path(import_id), 'import.log'), mimetype='text/plain', max_age=5)

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

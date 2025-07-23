
from flask import Blueprint, jsonify, request, Response #, send_file, session,
from tsx.api.util import db_session, get_user, get_roles, jsonify_rows, db_insert, db_update #, server_timezone, sanitise_file_name_string
from tsx.util import Bunch
from tsx.api.validation import *
from tsx.api.permissions import permitted
from sqlalchemy import text
from io import StringIO
import csv
import json

bp = Blueprint('documents', __name__)

@bp.route('/documents/data_agreements', methods = ['GET'])
def data_agreements():
	user = get_user()

	if not permitted(user, 'list', 'data_agreement'):
		return "Not authorised", 401

	include_draft = request.args.get('include_draft', 'false') == 'true'

	rows = db_session.execute(text("""
		SELECT
			JSON_ARRAYAGG(JSON_OBJECT(
				'id', id,
				'files', COALESCE((
					SELECT JSON_ARRAYAGG(
						JSON_OBJECT(
							'filename', filename,
							'upload_uuid', upload_uuid
						)
					)
					FROM data_agreement_file
					WHERE data_agreement_file.data_agreement_id = data_agreement.id
				), JSON_ARRAY()),
				'description', (
					SELECT filename
					FROM data_agreement_file
					WHERE data_agreement_file.data_agreement_id = data_agreement.id
					LIMIT 1
				),
				'commencement_date', provider_date_signed,
				'custodians', (
					SELECT JSON_ARRAYAGG(
						CONCAT(
							COALESCE(CONCAT(user.first_name, " ", user.last_name, " "), ""),
							COALESCE(CONCAT("<", user.email, ">"), "")
						)
					)
					FROM source_data_agreement, source, user_source, user
					WHERE source_data_agreement.data_agreement_id = data_agreement.id
					AND source.id = source_data_agreement.source_id
					AND user_source.source_id = source.id
					AND user.id = user_source.user_id
				),
				'sources', (
					SELECT JSON_ARRAYAGG(
						CONCAT(source.description, " (", source.id, ")")
					)
					FROM source_data_agreement, source
					WHERE source_data_agreement.data_agreement_id = data_agreement.id
					AND source.id = source_data_agreement.source_id
				),
				'is_draft', is_draft
			))
		FROM data_agreement
		WHERE %s
		AND (:include_draft OR NOT is_draft)
	""" % permission_clause), {
		'user_id': user.id,
		'include_draft': include_draft
	})

	[(result,)] = rows
	return Response(result or "[]", mimetype='application/json')

@bp.route('/documents/stats', methods = ['GET'])
def document_stats():
	user = get_user()

	if not permitted(user, 'list', 'data_agreement'):
		return "Not authorised", 401

	is_admin = 'Administrator' in get_roles(user)

	result = {}

	if is_admin:
		[(pending_uq_count,)] = db_session.execute(text("""
			SELECT COUNT(*)
			FROM source
			JOIN data_agreement_status ON data_agreement_status.id = source.data_agreement_status_id
			WHERE data_agreement_status.code = 'pending_uq_signature'
		"""))
		result['pending_uq_count'] = pending_uq_count

	[(data_agreement_count,)] = db_session.execute(text("""
		SELECT COUNT(*)
		FROM data_agreement
		WHERE %s
	""" % permission_clause), {
		'user_id': user.id
	})

	result['data_agreement_count'] = data_agreement_count

	return jsonify(result)

permission_clause = """
	(
		EXISTS (
			SELECT 1
			FROM user_role, role
			WHERE user_role.user_id = :user_id
			AND user_role.role_id = role.id
			AND role.description = 'Administrator'
		) OR EXISTS (
			SELECT 1
			FROM user_source
			JOIN source ON user_source.source_id = source.id
			JOIN data_agreement_status ON data_agreement_status_id = data_agreement_status.id
			JOIN source_data_agreement ON source_data_agreement.source_id
			WHERE user_source.user_id = :user_id
			AND source_data_agreement.data_agreement_id = data_agreement.id
			AND data_agreement_status.code = 'agreement_executed'
		)
	)
"""

def snake_to_capital_case(snake):
	parts = []
	for word in snake.split('_'):
		if word in ["id"]:
			parts.append(word.upper())
		else:
			parts.append(word.capitalize())
	return ''.join(parts)


@bp.route('/documents/data_agreements/<int:agreement_id>/csv', methods = ['GET'])
def agreement_csv(agreement_id=None):
	if agreement_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'view', 'data_agreement', agreement_id):
		return "Not authorised", 401

	data = get_agreement_json(agreement_id)

	if data == None:
		return "Not found", 404

	csv_data = {
		'DataAgreementID': agreement_id
	}

	for field in form_fields:
		csv_data[snake_to_capital_case(field.name)] = data.get(field.name, '')

	csv_data.pop('UploadUuid', None)


	output = StringIO()
	writer = csv.DictWriter(output, fieldnames=csv_data.keys())
	writer.writeheader()
	writer.writerow(csv_data)

	return Response(output.getvalue(),
		mimetype='application/csv',
		headers={
			"Content-Disposition": "attachment; filename=tsx_agreement_%s.csv" % agreement_id
		})

def select_field_clause(field):
	return "`%s`" % (field.name)

def map_fields(data, fields):
	for field in fields:
		if field.name in data:
			if field.type == 'boolean':
				if data[field.name] == 1:
					data[field.name] = True
				elif data[field.name] == 0:
					data[field.name] = False

def get_agreement_json(agreement_id):
	select_clauses = [select_field_clause(f) for f in backend_fields]
	select_clauses.append("`last_edited`")
	select_clauses.append("""
		(
			SELECT CONCAT(
				COALESCE(CONCAT(user.first_name, " ", user.last_name, " "), ""),
				COALESCE(CONCAT("<", user.email, ">"), "")
			)
			FROM user
			WHERE user.id = last_edited_by
		)
		AS `last_edited_by`
	""")
	select_clauses.append("""
		(
			SELECT JSON_ARRAYAGG(
				JSON_OBJECT(
					'filename', filename,
					'upload_uuid', upload_uuid
				)
			)
			FROM data_agreement_file
			WHERE data_agreement_file.data_agreement_id = data_agreement.id
		) AS `files`
		""")
	fields_sql = ", ".join(select_clauses)
	sql = "SELECT %s FROM data_agreement WHERE id = :id" % fields_sql
	rows = list(db_session.execute(text(sql), { "id": agreement_id }))

	if len(rows):
		data = dict(rows[0]._mapping)
		map_fields(data, backend_fields)
		data['has_expiry_date'] = data['expiry_date'] != None
		data['has_embargo_date'] = data['embargo_date'] != None
		data['files'] = json.loads(data['files'] or '[]')
		return data
	else:
		return None

@bp.route('/documents/data_agreements/<int:agreement_id>', methods = ['GET'])
def get_data_agreement(agreement_id=None):
	if agreement_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'view', 'data_agreement', agreement_id):
		return "Not authorised", 401

	data = get_agreement_json(agreement_id)

	if data:
		return jsonify(data)
	else:
		return "Not found", 404

@bp.route('/documents/data_agreements', methods = ['POST'])
def create_data_agreement():
	return create_or_update_data_agreement()

@bp.route('/documents/data_agreements/<int:agreement_id>', methods = ['PUT'])
def update_data_agreement(agreement_id=None):
	if agreement_id == None:
		return "Not found", 404

	return create_or_update_data_agreement(agreement_id)

def create_or_update_data_agreement(agreement_id=None):
	action = 'update' if agreement_id else 'create'

	user = get_user()

	if not permitted(user, action, 'data_agreement', agreement_id):
		return "Not authorised", 401

	if agreement_id:
		[(exists,)] = db_session.execute(text("""
			SELECT EXISTS (SELECT 1 FROM data_agreement WHERE id = :id)
		"""), { "id": agreement_id })
		if not exists:
			return "Not found", 404

	body = request.json

	context = Bunch()
	context.submitting = not body.get('is_draft', False)
	context.body = body
	errors = validate_fields(form_fields, body, context)

	if len(errors):
		return jsonify(errors), 400

	keys = [field.name for field in backend_fields]
	data = dict((key, body.get(key)) for key in keys)

	if agreement_id:
		data["id"] = agreement_id
		db_update('data_agreement', data, 'id')
	else:
		agreement_id = db_insert('data_agreement', data)

	db_session.execute(text("""
		UPDATE data_agreement
		SET last_edited_by = :user_id, last_edited = NOW()
		WHERE id = :agreement_id"""), {
		'user_id': user.id,
		'agreement_id': agreement_id
	})

	# Update files
	db_session.execute(text("""
		DELETE FROM data_agreement_file
		WHERE data_agreement_id = :agreement_id
		"""), {
		'agreement_id': agreement_id
	})

	for file in body.get('files'):
		db_session.execute(text("""
			INSERT INTO data_agreement_file (data_agreement_id, filename, upload_uuid)
			VALUES (:data_agreement_id, :filename, :upload_uuid)
		"""), {
			'data_agreement_id': agreement_id,
			'filename': file['filename'],
			'upload_uuid': file['upload_uuid']
		})

	db_session.commit()

	return jsonify(data), 200 if action == 'update' else 201


def val_required_for_submit(value, field, context):
	if context.submitting:
		return validate_required(value, field, context)

def val_required_if(other_field):
	def _validate_required_if(value, field, context):
		if context.body.get(other_field) == True:
			return validate_required(value, field, context)
	return _validate_required_if

def val_list(value, field, context):
	if value != None and type(value) != list:
		return "Must be a list"

def val_non_empty_for_submit(value, field, context):
	if context.submitting:
		if type(value) == list and len(value) == 0:
			return "Must contain at least one value"


form_fields = [
	Field(
		name='is_draft',
		validators=[]),
	Field(
		name='files',
		validators=[validate_required, val_list, val_non_empty_for_submit]),
	Field(
		name='ala_yes',
		type='boolean',
		validators=[val_required_for_submit, validate_boolean()]),
	Field(
		name='dcceew_yes',
		type='boolean',
		validators=[val_required_for_submit, validate_boolean()]),
	Field(
		name='conditions_raw',
		validators=[val_required_for_submit]),
	Field(
		name='conditions_sensitive',
		validators=[val_required_for_submit]),
	Field(
		name='has_expiry_date',
		validators=[validate_boolean()]),
	Field(
		name='expiry_date',
		validators=[validate_date(), val_required_if('has_expiry_date')]),
	Field(
		name='has_embargo_date',
		validators=[validate_boolean()]),
	Field(
		name='embargo_date',
		validators=[validate_date(), val_required_if('has_embargo_date')]),
	Field(
		name='provider_name',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_position',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_organisation',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_email',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_phone',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_postal_address',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_abn',
		validators=[validate_max_chars(32)]),
	Field(
		name='data_description'),
	Field(
		name='provider_signatory',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_witness',
		validators=[validate_max_chars(255)]),
	Field(
		name='provider_date_signed',
		validators=[validate_date()]),
	Field(
		name='uq_signatory',
		validators=[validate_max_chars(255)]),
	Field(
		name='uq_witness',
		validators=[validate_max_chars(255)]),
	Field(
		name='uq_date_signed',
		validators=[validate_date()])
]

backend_fields = [f for f in form_fields if f.name not in ["has_expiry_date", "has_embargo_date", "files"]]

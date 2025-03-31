from flask import Blueprint, jsonify, request, session
from tsx.api.util import db_session, get_user, jsonify_rows
from tsx.api.permissions import permitted
from tsx.db import MonitoringProgram, User
from tsx.api.validation import *
from sqlalchemy import text

bp = Blueprint('program', __name__)

program_fields = [
	Field(name='description', title='Program name', validators=[validate_required, validate_max_chars(255)]),
	Field(name='summary', title='Program summary', validators=[validate_max_chars(4096)]),
	Field(name='lead', title='Program lead', validators=[validate_max_chars(255)])
]

@bp.route('/monitoring_programs/<int:program_id>', methods = ['GET'])
def get_program(program_id=None):
	user = get_user()

	if not permitted(user, 'get', 'program', program_id):
		return "Not authorised", 401

	program = db_session.query(MonitoringProgram).get(program_id) if program_id else None

	if program == None:
		return "Not found", 404

	result = program_to_json(program)

	result['can_delete'] = permitted(user, 'delete', 'program', program_id)
	result['can_manage_managers'] = permitted(user, 'manage_managers', 'program', program_id)

	return jsonify(result), 200


@bp.route('/monitoring_programs', methods = ['POST'])
def create_monitoring_program():
	return create_or_update_program()



@bp.route('/monitoring_programs/<int:program_id>', methods = ['PUT'])
def update_monitoring_program(program_id = None):
	if program_id == None:
		return "Not found", 404

	return create_or_update_program(program_id)

@bp.route('/monitoring_programs/<int:program_id>', methods = ['DELETE'])
def delete_monitoring_program(program_id = None):
	if program_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'delete', 'program', program_id):
		return "Not authorised", 401

	db_session.execute(text("""DELETE FROM monitoring_program WHERE id = :program_id"""), { 'program_id': program_id })
	db_session.commit()

	return "OK", 200

@bp.route('/monitoring_programs/<int:program_id>/sources/<int:source_id>', methods = ['DELETE'])
def remove_source_from_monitoring_program(program_id = None, source_id = None):
	if program_id == None or source_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'update', 'source', program_id):
		return "Not authorised", 401

	db_session.execute(text("""UPDATE source SET monitoring_program_id = NULL WHERE id = :source_id AND monitoring_program_id = :program_id"""),
		{ 'program_id': program_id, 'source_id': source_id })
	db_session.commit()

	return "OK", 200

@bp.route('/monitoring_programs/<int:program_id>/managers/<int:user_id>', methods = ['DELETE'])
def remove_manager_from_monitoring_program(program_id = None, user_id = None):
	if program_id == None or user_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'mangage_managers', 'program', program_id):
		return "Not authorised", 401

	db_session.execute(text("""DELETE FROM user_program_manager WHERE user_id = :user_id AND monitoring_program_id = :program_id"""),
		{ 'program_id': program_id, 'user_id': user_id })
	db_session.commit()

	return "OK", 200

@bp.route('/monitoring_programs/<int:program_id>/managers', methods = ['POST'])
def add_manager_to_monitoring_program(program_id = None):
	if program_id == None:
		return "Not found", 404

	user = get_user()

	if not permitted(user, 'mangage_managers', 'program', program_id):
		return "Not authorised", 401

	body = request.json

	email = body["email"]

	if not re.match(email_regex, email):
		return jsonify({ 'error' : '"%s" is not a valid email address' % email }), 400

	manager = db_session.query(User).filter(User.email == email).one_or_none()

	if not manager:
		manager = User(email=email)
		db_session.add(manager)
		db_session.flush()

	db_session.execute(text("""REPLACE INTO user_program_manager (user_id, monitoring_program_id) VALUES (:user_id, :program_id)"""),
		{ 'user_id': manager.id, 'program_id': program_id })
	db_session.commit()

	return "OK", 201


def create_or_update_program(program_id=None):
	action = 'update' if program_id else 'create'

	user = get_user()

	if not permitted(user, action, 'program', program_id):
		return "Not authorised", 401

	if program_id:
		program = db_session.query(MonitoringProgram).get(program_id)
	else:
		program = MonitoringProgram()

	if not program:
		return "Not found", 400

	body = request.json

	errors = validate_fields(program_fields, body)

	if len(errors):
		return jsonify(errors), 400

	update_program_from_json(program, body)
	db_session.add(program)
	db_session.flush()

	if action == 'create':
		db_session.execute(text("""INSERT INTO user_program_manager (user_id, monitoring_program_id) VALUES (:user_id, :program_id)"""),
				{ 'program_id': program.id, 'user_id': user.id })


	db_session.commit()

	return jsonify(program_to_json(program)), 200 if program_id else 201

def update_program_from_json(program, json):
	for field in program_fields:
		value = json.get(field.name)
		if type(value) == str:
			value = value.strip()
		setattr(program, field.name, value)

def program_to_json(program):
	json = { 'id': program.id }
	for field in program_fields:
		json[field.name] = getattr(program, field.name)
	return json

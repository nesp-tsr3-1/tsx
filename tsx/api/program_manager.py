from flask import Blueprint, request
from tsx.api.util import db_session, get_user, jsonify_rows

from tsx.api.permissions import permitted
from sqlalchemy import text

bp = Blueprint('program_manager', __name__)

@bp.route('/programs/<int:program_id>/managers', methods = ['GET'])
def get_program_managers(program_id = None):
	user = get_user()

	if not permitted(user, 'list_managers', 'program', program_id):
		return "Not authorised", 401

	if program_id is None:
		return "Not found", 404

	rows = db_session.execute(text("""
		SELECT user.id, email, first_name, last_name
		FROM user, user_program_manager
		WHERE user.id = user_id
		AND monitoring_program_id = :program_id"""), { "program_id": program_id })

	return jsonify_rows(rows)


@bp.route('/users/<int:user_id>/programs', methods = ['GET'])
def get_programs(user_id = None):
	user = get_user()

	if not permitted(user, 'list_programs', 'user', user_id):
		return "Not authorised", 401

	if user_id is None:
		return "Not found", 404

	rows = db_session.execute(text("""
		SELECT monitoring_program.id, description
		FROM monitoring_program, user_program_manager
		WHERE monitoring_program.id = monitoring_program_id
		AND user_id = :user_id"""), { "user_id": user_id })

	return jsonify_rows(rows)

@bp.route('/users/<int:user_id>/programs', methods = ['PUT'])
def update_programs(user_id = None):
	user = get_user()

	if not permitted(user, 'update_programs', 'user', user_id):
		return "Not authorised", 401

	if user_id is None:
		return "Not found", 404

	body = request.json

	db_session.execute(text("""DELETE FROM user_program_manager WHERE user_id = :user_id"""), { "user_id": user_id })
	for program_id in body:
		db_session.execute(
			text("""INSERT INTO user_program_manager (user_id, monitoring_program_id) VALUES (:user_id, :program_id)"""),
			{
				"user_id": user_id,
				"program_id": program_id
			})
	db_session.commit()

	return "OK", 201

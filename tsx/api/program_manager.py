from flask import Blueprint, jsonify, request, session
from tsx.api.util import db_session, get_user

from tsx.api.permissions import permitted

bp = Blueprint('program_manager', __name__)

def jsonify_rows(rows):
	return jsonify([dict(row) for row in rows])

@bp.route('/programs/<int:program_id>/managers', methods = ['GET'])
def get_program_managers(program_id = None):
	user = get_user()

	if not permitted(user, 'list_managers', 'program', program_id):
		return "Not authorized", 401

	if program_id == None:
		return "Not found", 404

	rows = db_session.execute("""
		SELECT user.id, email, first_name, last_name
		FROM user, user_program_manager
		WHERE user.id = user_id
		AND monitoring_program_id = :program_id""", { "program_id": program_id })

	return jsonify_rows(rows)


@bp.route('/users/<int:user_id>/programs', methods = ['GET'])
def get_programs(user_id = None):
	user = get_user()

	if not permitted(user, 'list_programs', 'user', user_id):
		return "Not authorized", 401

	if user_id == None:
		return "Not found", 404

	rows = db_session.execute("""
		SELECT monitoring_program.id, description
		FROM monitoring_program, user_program_manager
		WHERE monitoring_program.id = monitoring_program_id
		AND user_id = :user_id""", { "user_id": user_id })

	return jsonify_rows(rows)

@bp.route('/users/<int:user_id>/programs', methods = ['PUT'])
def update_programs(user_id = None):
	user = get_user()

	if not permitted(user, 'update_programs', 'user', user_id):
		return "Not authorized", 401

	if user_id == None:
		return "Not found", 404

	body = request.json

	db_session.execute("""DELETE FROM user_program_manager WHERE user_id = :user_id""", { "user_id": user_id })
	for program_id in body:
		db_session.execute(
			"""INSERT INTO user_program_manager (user_id, monitoring_program_id) VALUES (:user_id, :program_id)""",
			{
				"user_id": user_id,
				"program_id": program_id
			})
	db_session.commit()

	return "OK", 201

from tsx.api.util import db_session, get_roles
from tsx.db import DataProcessingNotes
from sqlalchemy import text

def is_program_manager_of_source(user_id, source_id):
	return len(db_session.execute(
		text("""SELECT 1 FROM user_program_manager, source
		WHERE user_id = :user_id
		AND source.monitoring_program_id = user_program_manager.monitoring_program_id
		AND source.id = :source_id"""), {
		'source_id': source_id,
		'user_id': user_id
		}).fetchall()) > 0

def is_program_manager_of_program(user_id, monitoring_program_id):
	return len(db_session.execute(
		text("""SELECT 1 FROM user_program_manager
		WHERE user_id = :user_id
		AND monitoring_program_id = :monitoring_program_id"""), {
		'monitoring_program_id': monitoring_program_id,
		'user_id': user_id
		}).fetchall()) > 0

def is_custodian_of_source(user_id, source_id):
	return len(db_session.execute(
		text("""SELECT 1 FROM user_source
		WHERE user_id = :user_id
		AND source_id = :source_id"""), {
		'source_id': source_id,
		'user_id': user_id
		}).fetchall()) > 0

def permitted(user, action, resource_type, resource_id=None):
	if user == None:
		return False

	user_roles = get_roles(user)
	if 'Administrator' in user_roles:
		return True

	if resource_type == 'source':
		if 'Program manager' in user_roles:
			if action in ('create', 'list'):
				return True
			if action in ('get', 'update', 'download_data'):
				return resource_id != None and is_program_manager_of_source(user.id, resource_id)

		if 'Custodian' in user_roles:
			if action in ('create', 'list'):
				return True
			if action in ('get', 'update', 'delete', 'import_data', 'manage_custodians', 'download_data'):
				return resource_id != None and is_custodian_of_source(user.id, resource_id)

	if resource_type == 'user':
		if action in ('list_programs'):
			return True

	if resource_type == 'program':
		if action in ('list_managers'):
			return True
		if action in ('download_data', 'update'):
			return is_program_manager_of_program(user.id, resource_id)
		if action in ('create'):
			return 'Program manager' in user_roles


	if resource_type == 'notes' and 'Custodian' in user_roles:
		try:
			notes = db_session.query(DataProcessingNotes).get(resource_id)
			return notes.user_id == user.id
		except:
			return False

	return False

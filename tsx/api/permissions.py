from tsx.api.util import db_session, get_roles
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

def is_custodian_of_form(user_id, form_id):
	return len(db_session.execute(
		text("""SELECT 1 FROM custodian_feedback
		JOIN user_source ON user_source.source_id = custodian_feedback.source_id
		WHERE custodian_feedback.id = :form_id
		AND user_source.user_id = :user_id"""), {
		'form_id': form_id,
		'user_id': user_id
		}).fetchall()) > 0

def permitted(user, action, resource_type, resource_id=None):
	if user == None:
		return False

	user_roles = get_roles(user)
	if 'Administrator' in user_roles:
		return True

	if resource_type == 'source':
		if action in ('create', 'list'):
			return True
		if action in ('get', 'update', 'download_data'):
			return resource_id != None and (is_program_manager_of_source(user.id, resource_id) or is_custodian_of_source(user.id, resource_id))
		if action in ('delete', 'import_data', 'manage_custodians'):
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

	if resource_type == 'custodian_feedback_dataset':
		if action in ('list'):
			return True
		if action in ('view'):
			(source_id, taxon_id) = resource_id.split('_', 1)
			return is_custodian_of_source(user.id, source_id)

	if resource_type == 'custodian_feedback_form':
		if action in ('view', 'update'):
			return resource_id != None and is_custodian_of_form(user.id, resource_id)

	if resource_type == 'data_agreement':
		if action in ('list'):
			return True

	if resource_type == 'acknowledgement_letter':
		if action in ('list'):
			return True

	return False

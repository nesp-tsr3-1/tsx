from flask import request, make_response, g, jsonify, Blueprint
from tsx.db import get_session
from tsx.api.util import db_session
import os
import json

bp = Blueprint('misc', __name__)

def query_to_json(query):
	return jsonify([dict(row) for row in db_session.execute(query)])

@bp.route('/region', methods = ['GET'])
def get_region():
	return query_to_json("""SELECT id, name, state FROM region""")

@bp.route('/search_type', methods = ['GET'])
@bp.route('/searchtype', methods = ['GET'])
def get_search_type():
	return query_to_json("""SELECT id, description AS name FROM search_type""")

@bp.route('/species', methods = ['GET'])
def get_species():
	q = request.args.get('q', type=str)
	if q == 'all_present':
		return query_to_json("""SELECT id, common_name, scientific_name
			FROM taxon
			WHERE (id IN (SELECT taxon_id FROM t1_sighting) or id in (SELECT taxon_id FROM t2_sighting))
			ORDER BY COALESCE(common_name, scientific_name)
		""")
	elif q == 't1_present':
		return query_to_json("""SELECT id, common_name, scientific_name
			FROM taxon
			WHERE (id IN (SELECT taxon_id FROM t1_sighting))
			ORDER BY COALESCE(common_name, scientific_name)
		""")
	else:
		return query_to_json("""SELECT spno, common_name
			FROM taxon
			WHERE spno IS NOT NULL
			AND common_name IS NOT NULL
			ORDER BY common_name
		""")

@bp.route('/response_variable_type', methods = ['GET'])
@bp.route('/responsevariabletype', methods = ['GET'])
def get_response_variable():
	return query_to_json("""SELECT id, description FROM response_variable_type""")

@bp.route('/status', methods = ['GET'])
def get_status():
	return query_to_json("""SELECT id, description FROM taxon_status""")

@bp.route('/source', methods = ['GET'])
def get_source():
	return query_to_json("""SELECT id, source_type_id, provider, description FROM source ORDER BY description""")

@bp.route('/monitoring_program', methods = ['GET'])
def get_monitoring_program():
	return query_to_json("""
		SELECT id,
			description,
			(SELECT COUNT(*) FROM source WHERE monitoring_program_id = monitoring_program.id) AS source_count
		FROM monitoring_program
		ORDER BY description""")

@bp.route('/intensive_management_group', methods = ['GET'])
def get_intensive_management_group():
	return query_to_json("""SELECT DISTINCT `grouping` AS description FROM intensive_management WHERE `grouping` IS NOT NULL ORDER BY description""")

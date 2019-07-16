from flask import request, make_response, g, jsonify, Blueprint
from tsx.db import get_session
import os
import json

bp = Blueprint('misc', __name__)

def query_to_json(query):
	session = get_session()
	result = [dict(zip(row.keys(), row.values())) for row in session.execute(query).fetchall()]
	# result = [{**row} for row in session.execute(query).fetchall()] # Python 3 version
	session.close()
	return jsonify(result)

@bp.route('/region', methods = ['GET'])
def get_region():
	return query_to_json("""SELECT id, name, state FROM region""")

@bp.route('/search_type', methods = ['GET'])
@bp.route('/searchtype', methods = ['GET'])
def get_search_type():
	return query_to_json("""SELECT id, description AS name FROM search_type""")

@bp.route('/species', methods = ['GET'])
def get_species():
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

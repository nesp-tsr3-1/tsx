from flask import request, make_response, g, jsonify, Blueprint
from nesp.db import get_session
import os
import json
# this is going to use quite alot of RAM, but it is more responsive than using dask
bp = Blueprint('misc', __name__)

@bp.route('/region', methods = ['GET'])
def get_subibra():
	session = get_session()
	rows = session.execute("""SELECT id, name, state FROM region""").fetchall()
	region_info = []
	for id, name, state in rows:
		region_info.append({'id': int(id), 'name': name, 'state': state})
	session.close()
	return jsonify(region_info)


@bp.route('/searchtype', methods = ['GET'])
def get_searchtype():
	session = get_session()
	rows = session.execute("""SELECT id, description FROM search_type""").fetchall()
	searchtype_info = []
	for searchtype_id, name in rows:
		searchtype_info.append({'id': int(searchtype_id), 'name': name})
	session.close()
	return jsonify(searchtype_info)
	

@bp.route('/species', methods = ['GET'])
def get_species():
	session = get_session()
	rows = session.execute("""SELECT spno, common_name FROM taxon""").fetchall()
	species_info = []
	for spno, common_name in rows:
		species_info.append({'spno': int(spno), 'common_name': common_name})
	session.close()
	return jsonify(species_info)
	

@bp.route('/responsevariabletype', methods = ['GET'])
def get_responsevariable():
	session = get_session()
	rows = session.execute("""SELECT id, description FROM response_variable_type""").fetchall()
	res_info = []
	for id, description in rows:
		res_info.append({'id': int(id), 'description': description})
	session.close()
	return jsonify(res_info)


@bp.route('/status', methods = ['GET'])
def get_status():
	session = get_session()
	rows = session.execute("""SELECT id, description FROM taxon_status""").fetchall()
	res_info = []
	for id, description in rows:
		res_info.append({'id': int(id), 'description': description})
	session.close()
	return jsonify(res_info)

@bp.route('/source', methods = ['GET'])
def get_source():
	session = get_session()
	rows = session.execute("""SELECT id, source_type_id, provider, description FROM source""").fetchall()
	res_info = []
	for id, source_type_id, provider, description in rows:
		res_info.append({'id': int(id), "source_type_id": int(source_type_id), 'provider': provider, 'description': description})
	session.close()
	return jsonify(res_info)
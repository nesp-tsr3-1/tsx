import csv
import StringIO
from flask import request, make_response, g, jsonify, Blueprint
from nesp.api.util import csv_response
from nesp.db import get_session
from datetime import datetime
import nesp.config
import pandas as pd
import os
import json
# this is going to use quite alot of RAM, but it is more responsive than using dask
bp = Blueprint('lpi_data', __name__)
export_dir = nesp.config.data_dir('export')
filename = 'lpi.csv'
df = pd.read_csv(os.path.join(export_dir, filename), index_col = 'ID', 
	dtype={'ID': str, 'SpNo': int, 'TaxonID': str, 'CommonName': str, 'SiteDesc': str,
			'SourceDesc': str,'SubIBRA': str,'Unit': str,'SearchTypeDesc': str,'SpatialAccuracyInM': float,
			'ExperimentalDesignType': str,'ResponseVariableType': str,'DataType': str})


@bp.route('/lpi-data', methods = ['GET'])
def lpi_data():
	"""Output aggregated data in LPI wide format"""
	#output forat: csv or json
	output_format = request.args.get('format', type=str)
	download_file = request.args.get('download', type=str)
	#filter: species, state, searchtype
	filter_str = ""
	#spno
	filters = []
	if(request.args.has_key('spno')):
		_sp_no = request.args.get('spno', type=int)
		filters.append("SpNo=='%d'" % (_sp_no))
	#state
	if(request.args.has_key('state')):
		filters.append("State=='%s'" % (request.args.get('state', type=str)))
	#searchtypedesc
	if(request.args.has_key('searchtype')):
		_search_type = request.args.get('searchtype', type=int)
		# find in database
		session = get_session()
		_search_type_desc = session.execute(
            """SELECT * FROM search_type WHERE id = :searchtypeid""", 
            {'searchtypeid': _search_type}).fetchone()['description']
		filters.append("SearchTypeDesc=='%s'" % (_search_type_desc))
	#subibra
	if(request.args.has_key('subibra')):
		_subibra = request.args.get('subibra', type=str)
		filters.append("SubIBRA=='%s'" % (_subibra))
	
	#create filters
	filtered_dat = None
	if len(filters) > 0:
		filters_str = " and ".join(filters)
		filtered_dat = df.query(filters_str) 
	else:
		filtered_dat = df
	if output_format == None or output_format == 'csv':
		if download_file == None or download_file == "":
			return filtered_dat.to_csv()
		else:
			output = make_response(filtered_dat.to_csv())
			output.headers["Content-Disposition"] = "attachment; filename=%s" % download_file
			output.headers["Content-type"] = "text/csv"
			return output
	elif output_format == "json":
		#pandas index data a bit different, so need to unfold it, can use json_pandas for direct export
		json_data = json.loads(filtered_dat.to_json())
		return_json = {}
		for field, value in json_data.items():
			for _timeserie_id, _item_value in value.items():
				if not return_json.has_key(_timeserie_id):
					return_json[_timeserie_id] = {}
				return_json[_timeserie_id][field] = _item_value
		return jsonify(return_json)
	elif output_format == 'json_pandas':
		return filtered_dat.to_json()
	else:
		return jsonify("Unsupported format (Supported: csv, json)"), 400







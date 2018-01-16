import csv
import StringIO
from flask import request, make_response, g, jsonify, Blueprint
from nesp.api.util import csv_response
from nesp.db import get_session
from datetime import datetime
from nesp.util import run_parallel
import nesp.config
import pandas as pd
import os
import json
import numpy as np

# this is going to use quite alot of RAM, but it is more responsive than using dask
bp = Blueprint('lpi_data', __name__)
export_dir = nesp.config.data_dir('export')
filename = 'lpi-filtered.csv'
df = pd.read_csv(os.path.join(export_dir, filename), index_col = 'ID',quoting=csv.QUOTE_MINIMAL, 
	dtype={'ID': int, 'Binomial': str, 'SpNo': int, 'TaxonID': str, 'CommonName': str, 
		'Class': str, 'Order': str, 'Family': str, 'FamilyCommonName': str, 
		'Genus': str, 'Species': str, 'Subspecies': str,  
		'FunctionalGroup': str, 'FunctionalSubGroup': str, 'EPBCStatus': str, 'IUCNStatus': str, 'BirdLifeAustraliaStatus': str,
		'MaxStatus': str, 'State': str, 'Region': str, 'Latitude': float, 'Longitude': float, 'SiteID': int, 'SiteDesc': str,
		'SourceID': int, 'SourceDesc': str, 'UnitID': int, 'Unit': str, 'SearchTypeID': str, 'SearchTypeDesc': str, 'ExperimentalDesignType': str,
		'ExperimentalDesignType': str,'ResponseVariableType': str, 'DataType': int, 'TimeSeriesLength': float,
		'TimeSeriesSampleYears': float ,'TimeSeriesCompleteness': float,'TimeSeriesSamplingEvenness': float,
		'NoAbsencesRecorded': str,'StandardisationOfMethodEffort': str,'ObjectiveOfMonitoring': str,'SpatialRepresentativeness': float, 'SeasonalConsistency': float,
		'SpatialAccuracy':float,'ConsistencyOfMonitoring': float,'MonitoringFrequencyAndTiming': float, 'DataAgreement': str, 'SurveysCentroidLatitude': float, 
		'SurveysCentroidLongitude': float, 'SurveyCount': int, 'TimeSeriesID': str, 'NationalPriorityTaxa': int})


@bp.route('/lpi-data', methods = ['GET'])
def lpi_data():
	"""Output aggregated data in LPI wide format"""
	#output format: csv or json
	output_format = request.args.get('format', type=str)
	download_file = request.args.get('download', type=str)

	# Filter LPI data based on request parameters
	filtered_dat = get_filtered_data()

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
		json_data = json.loads(unicode(filtered_dat.to_json(), errors='ignore'))
		return_json = {}
		for field, value in json_data.items():
			for _timeserie_id, _item_value in value.items():
				if not return_json.has_key(_timeserie_id):
					return_json[_timeserie_id] = {}
				return_json[_timeserie_id][field] = _item_value
		return jsonify(return_json)
	elif output_format == 'json_pandas':
		return filtered_dat.to_json()
	# This will be removed
	elif output_format == 'dotplot':
		json_data = json.loads(unicode(filtered_dat.to_json(), errors='ignore'))
		plot_dat = []
		years = sorted([ y for y in json_data.keys() if y.isdigit() ])
		binomials = json_data['Binomial']
		for year in years:
			for _timeserie_id, _item_value in json_data[year].items():
				if _item_value != None:
					plot_dat.append({"ID": _timeserie_id, "year": year, "Binomial": binomials[_timeserie_id], "count": _item_value})
		return json.dumps(plot_dat)
	# TODO: replace dotplot with plot
	elif output_format == 'plot':
		json_data = json.loads(unicode(filtered_dat.to_json(), errors='ignore'))
		dotplot_dat = []
		timeseries_year = {}
		species_year = {}
		species_count_year = {}
		taxa_count_year = {}
		taxa_year = {}
		years = sorted([ y for y in json_data.keys() if y.isdigit() ])
		binomials = json_data['Binomial']
		species = json_data['SpNo']
		taxa = json_data['TaxonID']
		for year in years:
			for _timeserie_id, _item_value in json_data[year].items():
				if _item_value != None:
					dotplot_dat.append({"ID": _timeserie_id, "year": year, "Binomial": binomials[_timeserie_id], "count": _item_value})
					if year in timeseries_year.keys():
						timeseries_year[year] = timeseries_year[year] + 1
						species_year[year].add(species[_timeserie_id])
						taxa_year[year].add(taxa[_timeserie_id])
					else:
						timeseries_year[year] = 1
						species_year[year] = set([species[_timeserie_id]])
						taxa_year[year] = set([taxa[_timeserie_id]])
		# print (species_year)
		for year in years:
			if year in species_year.keys():
				species_count_year[year] = len(species_year[year])
				taxa_count_year[year] = len(taxa_year[year])
			#else:
			#	species_count_year[year] = 0
			#	timeseries_year[year] =0
		summaryplot_dat = {'species': species_count_year, 'timeseries': timeseries_year, 'taxa': taxa_count_year}
		return_json={'summary': summaryplot_dat, 'dotplot': dotplot_dat}
		return json.dumps(return_json)
	else:
		return jsonify("Unsupported format (Supported: csv, json)"), 400

@bp.route('/lpi-data/plot', methods = ['GET'])
def plot():
	# Filter data
	df = get_filtered_data()

	return json.dumps({
		'dotplot': get_dotplot_data(df),
		'summary': get_summary_data(df)
	})


def get_dotplot_data(filtered_data):
	"""Converts time-series to a minimal form for generating dot plots:
	[
		[[year,count],[year,count] .. ],
		...
	]
	Where count = 0 or 1
	"""
	df = filtered_data

	if len(df) == 0:
		return []

	# Get year columns
	years = [col for col in df.columns if col.isdigit()]
	int_years = [int(year) for year in years]

	# Experiment: order dot plot data to get a better visual indicator
	df = df.loc[:,years]
	m = (df >= 0).values
	c = (2 ** np.arange(0, 70, dtype=object))
	df = df.assign(x = m.dot(c)).sort_values(['x'])

	# Convert Pandas data to numpy array so we can iterate over it efficiently
	raw_data = df.loc[:,years].values
	result = []
	for i, row in enumerate(raw_data):
		result.append([[int_years[j], 1 if value > 0 else 0] for j, value in enumerate(row) if value >= 0])


	return result

def get_summary_data(filtered_data):
	"""Calculates the number of time-series and distinct taxa per year"""

	df = filtered_data

	if len(df) == 0:
		return {
			'timeseries': {},
			'taxa': {}
		}

	# Get year columns
	years = [col for col in df.columns if col.isdigit()]

	return {
		# Get number of time series per year
		'timeseries': df.loc[:,years].count().to_dict(),

		# Get number of unique taxa per year
		#
		# There is a bit to unpack in this line:
		#    df.loc[:,['TaxonID'] + years]   -- Filter down to just year and taxon id columns
		#    groupby('TaxonID').count() > 0  -- Group on taxon ID to get a matrix of Taxa x Year with True/False in each cell
		#    sum()                           -- Finally count up totals for each year
		'taxa': (df.loc[:,['TaxonID'] + years].groupby('TaxonID').count() > 0).sum().to_dict()
	}

def get_filtered_data():
	filter_str = build_filter_string()
	if filter_str:
		return df.query(filter_str)
	else:
		return df

def build_filter_string():
	filter_str = ""
	#spno
	filters = []
	if request.args.has_key('spno'):
		_sp_no = request.args.get('spno', type=int)
		filters.append("SpNo=='%d'" % (_sp_no))
	if request.args.has_key('datatype'):
		_sp_no = request.args.get('datatype', type=int)
		filters.append("DataType=='%d'" % (_sp_no))
	#state
	if request.args.has_key('state'):
		filters.append("State=='%s'" % (request.args.get('state', type=str)))
	#searchtypedesc
	if request.args.has_key('searchtype'):
		_search_type = request.args.get('searchtype', type=int)
		# find in database
		session = get_session()
		_search_type_desc = session.execute(
            """SELECT * FROM search_type WHERE id = :searchtypeid""",
            {'searchtypeid': _search_type}).fetchone()['description']
		filters.append("SearchTypeDesc=='%s'" % (_search_type_desc))
		session.close()
	#subibra
	if request.args.has_key('subibra'):
		_subibra = request.args.get('subibra', type=str)
		filters.append("SubIBRA=='%s'" % (_subibra))

	#sourceid
	if request.args.has_key('sourceid'):
		_sourceid = request.args.get('sourceid', type=int)
		filters.append("SourceID=='%d'" % (_sourceid))

	# Functional group
	if request.args.has_key('group'):
		_group = request.args.get('group', type=str)
		filters.append("FunctionalGroup=='%s'" % (_group))

	# functional subgroup
	if request.args.has_key('subgroup'):
		_subgroup = request.args.get('subgroup', type=str)
		filters.append("FunctionalSubGroup=='%s'" % (_subgroup))

	#statusauth
	_status = None
	if request.args.has_key('status'):
		_status = request.args.get('status', type=str)

	if _status!= None and request.args.has_key('statusauth'): #IUCN, EPBC, BirdLifeAustralia, Max
		_statusauth = request.args.get('statusauth', type=str)
		if _statusauth == "IUCN" :
			filters.append("IUCNStatus=='%s'" % (_status))
		elif _statusauth == "EPBC":
			filters.append("EPBCStatus=='%s'" % (_status))
		elif _statusauth == "BirdLifeAustralia":
			filters.append("BirdLifeAustraliaStatus=='%s'" % (_status))
		else:
			filters.append("MaxStatus=='%s'" % (_status))
	# national priority
	if request.args.has_key('priority'):
		filters.append("NationalPriorityTaxa=='%d'" %(request.args.get('priority', type=int)))

	if len(filters) > 0:
		return " and ".join(filters)
	else:
		return None

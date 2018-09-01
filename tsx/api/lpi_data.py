# -*- coding: UTF-8 -*-
import csv
import StringIO
from flask import request, make_response, g, jsonify, Blueprint
from tsx.api.util import csv_response
from tsx.db import get_session
from datetime import datetime
from tsx.util import run_parallel
import tsx.config
import pandas as pd
import os
import json
import numpy as np

# this is going to use quite alot of RAM, but it is more responsive than using dask
bp = Blueprint('lpi_data', __name__)
export_dir = tsx.config.data_dir('export')
filename = 'lpi-filtered.csv'
# filename = '/Users/james/tmp/lpi-2018-08-08/lpi-filtered.csv'
unfiltered_df = pd.read_csv(os.path.join(export_dir, filename), index_col = 'ID',quoting=csv.QUOTE_MINIMAL, 
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

# Important: remove sensitive information that must not be exposed publicly
unfiltered_df = unfiltered_df.drop(['SurveysCentroidLatitude', 'SurveysCentroidLongitude', 'DataAgreement'], axis=1)

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

@bp.route('/lpi-data/intensity', methods = ['GET'])
def get_intensity():
	filtered_data = get_filtered_data()
	if len(filtered_data) == 0:
		return []
	dat = filtered_data.to_dict()
	ids = dat['TimeSeriesID'].values() 
	session = get_session()
	result = session.execute("""SELECT time_series_id, start_date_y as Year, ST_X(centroid_coords) as Latitude, 
				    ST_Y(centroid_coords) as Longitude, SUM(survey_count) as Count
				    FROM aggregated_by_year
				    WHERE include_in_analysis
				    AND time_series_id in %s 
				    GROUP BY time_series_id, Year, Latitude, Longitude"""%str(tuple(ids)))
	values = pd.DataFrame.from_records(data = result.fetchall(), columns = result.keys()).to_dict()
	session.close()
	# years = values['Year']
	lats = values['Latitude']
	longs = values['Longitude']
	counts = values['Count']
	years = values['Year']
	timeSeriesIDs = { id:[] for id in ids }
	results = {}
	for k, v in values['time_series_id'].iteritems():
		timeSeriesIDs[v].append(k)
	return json.dumps([ [lats[v[0]], longs[v[0]], [[years[i], int(counts[i])] for i in v]] for k, v in timeSeriesIDs.iteritems() if len(v) >0])

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
	df = df.loc[:,years]

	# Experiment - see email 'Dot plots - Random sampling of time series'

	# print sum(unfiltered_df.values >= 0)

	# sum_df = (df.fillna(0) * 0).head(50).values

	# n_runs = 100

	# for i in range(0,n_runs):
	# 	# Get random sample
	# 	df2 = df.assign(x = np.random.randn(len(df))).sort_values(['x']).head(50)

	# 	# Sort time series
	# 	m = (df2 >= 0).values
	# 	# c = (2 ** np.arange(0, len(df.columns), dtype=object)) # Order by last year surveyed
	# 	# c = np.arange(0, len(df.columns)) # Order by mean year surveyed
	# 	c = [1] * len(df2.columns) # Order by time sample years
	# 	x = m.dot(c)
	# 	# x = np.random.randn(len(df))
	# 	df2 = df2.assign(x = x).sort_values(['x'])

	# 	sum_df += (df2.loc[:,years] >= 0).values

	# raw_data = sum_df - (n_runs / 2)


	# Get random sample
	df = df.assign(x = np.random.randn(len(df))).sort_values(['x']).head(50)

	# Sort time series
	m = (df >= 0).values
	# c = (2 ** np.arange(0, len(df.columns), dtype=object)) # Order by last year surveyed
	# c = np.arange(0, len(df.columns)) # Order by mean year surveyed
	c = [1] * len(df.columns) # Order by time sample years
	x = m.dot(c)
	# x = np.random.randn(len(df))
	df = df.assign(x = x).sort_values(['x'])

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

	# Fill in any gaps in time series
	# We are being a bit tricky here. We do a back-fill and forward-fill of values, and then add them together.
	# The NaNs propagate so that we end up with just the gaps filled with non-NaNs.
	# Note: We don't care about the actual values - just whether they are NaN or not.
	year_df = df.loc[:,years]
	year_df[years] = year_df.fillna(method='bfill', axis=1) + year_df.fillna(method='ffill', axis=1)
	year_df['TaxonID'] = df['TaxonID']
	df = year_df

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
		return unfiltered_df.query(filter_str)
	else:
		return unfiltered_df.copy()

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

@bp.route('/lpi-data/stats', methods = ['GET'])
def stats():
	# Filter data
	df = get_filtered_data()

	return json.dumps(get_stats(df))

@bp.route('/lpi-data/stats.html', methods = ['GET'])
def stats_html():
	# Filter data
	df = get_filtered_data()

	stats = get_stats(df)

	html = """
	<html>
		<head>
		</head>
		<body>
			<p>
				Time-series length (mean ± SD): {ts_length_mean:.1f} ± {ts_length_stddev:.1f}
			</p>
			<p>
				Number of samples (years) per time series (mean ± SD): {ts_years_mean:.1f} ± {ts_years_stddev:.1f}
			</p>
			<p>
				Number of data sources in Index: {num_sources}
			</p>
			<p>
				Number of taxa in Index: {num_taxa}
			</p>
			<table>
				<thead>
					<tr>
						<th>Taxon name</th>
						<th>Taxon scientific name</th>
						<th>Functional group</th>
						<th>Functional sub-group</th>
						<th>BirdLife Australia status</th>
						<th>EPBC status</th>
						<th># data sources</th>
						<th># time series</th>
						<th>Mean time-series length</th>
						<th>Spatial representativeness</th>
					</tr>
				</thead>
				<tbody>
	""".format(
		ts_length_mean = stats['ts_length']['mean'],
		ts_length_stddev = stats['ts_length']['stddev'],
		ts_years_mean = stats['ts_years']['mean'],
		ts_years_stddev = stats['ts_years']['stddev'],
		num_sources = stats['num_sources'],
		num_taxa = stats['num_taxa']
	)

	for row in stats['taxa_with_data']:
		html += """
		<tr>
			<td>{common_name}</td>
			<td>{scientific_name}</td>
			<td>{bird_group}</td>
			<td>{bird_sub_group}</td>
			<td>{aust_status}</td>
			<td>{epbc_status}</td>
			<td>{num_sources:.0f}</td>
			<td>{num_ts:.0f}</td>
			<td>{ts_length_mean:.1f}</td>
			<td>{spatial_rep:.1f}</td>
		</tr>""".format(**row)

	for row in stats['taxa_without_data']:
		html += """
		<tr>
			<td>{common_name}</td>
			<td>{scientific_name}</td>
			<td>{bird_group}</td>
			<td>{bird_sub_group}</td>
			<td>{aust_status}</td>
			<td>{epbc_status}</td>
			<td>0</td>
			<td>0</td>
			<td></td>
			<td></td>
		</tr>""".format(**row)

	html += """
				</tbody>
			</table>
		</body>
	</html>
	"""

	return html

def get_stats(filtered_data):
	df = filtered_data

	years = [col for col in df.columns if col.isdigit()]
	int_years = [int(year) for year in years]

	year_df = df.loc[:,years] * 0 + int_years

	# Time series length
	ts_length = df['TimeSeriesLength'] # year_df.max(axis = 1) - year_df.min(axis = 1) + 1

	# Time series sample years
	ts_years = df['TimeSeriesSampleYears'] # (year_df * 0 + 1).sum(axis = 1)

	n_sources = df['SourceDesc'].nunique()
	n_taxa = df['TaxonID'].nunique()

	grouped_by_taxon = df.groupby('TaxonID').agg({
		'TimeSeriesLength': np.mean,
		'SourceDesc': lambda x: x.nunique(),
		'TimeSeriesID': lambda x: x.nunique(),
		'SpatialRepresentativeness': np.mean
	}).rename(columns = {
		'TimeSeriesLength': 'ts_length_mean',
		'SourceDesc': 'num_sources',
		'TimeSeriesID': 'num_ts',
		'SpatialRepresentativeness': 'spatial_rep'
	})

	session = get_session()
	result = session.execute("""SELECT
			id AS 'TaxonID',
			common_name,
			scientific_name,
			bird_group,
			bird_sub_group,
			(SELECT description FROM taxon_status WHERE taxon_status.id = aust_status_id) AS aust_status,
			(SELECT description FROM taxon_status WHERE taxon_status.id = epbc_status_id) AS epbc_status
		FROM taxon
		WHERE GREATEST(COALESCE(aust_status_id, 0), COALESCE(epbc_status_id, 0), COALESCE(iucn_status_id, 0)) NOT IN (0,1,7)
		AND (ultrataxon OR taxon.id IN :taxon_ids)""", {
			'taxon_ids': list(df['TaxonID'].unique())
		})
	session.close()

	all_taxa = pd.DataFrame.from_records(data = result.fetchall(), index = 'TaxonID', columns = result.keys())

	joined = all_taxa.join(grouped_by_taxon, how='outer').sort_values(['bird_group', 'bird_sub_group', 'common_name'], na_position='first')
	joined = joined.reset_index().rename(columns = { 'TaxonID': 'taxon_id' })
	joined['spatial_rep'] *= 100

	taxa_with_data = joined.query('num_ts > 0')
	taxa_without_data = joined.query('num_ts != num_ts').drop(columns = ['ts_length_mean', 'num_sources', 'num_ts', 'spatial_rep'])

	return {
		'num_sources': df['SourceDesc'].nunique(),
		'num_taxa': df['TaxonID'].nunique(),
		'ts_length': {
			'mean': ts_length.mean(),
			'stddev': ts_length.std()
		},
		'ts_years': {
			'mean': ts_years.mean(),
			'stddev': ts_years.std()
		},
		'taxa_with_data': taxa_with_data.to_dict(orient='records'),
		'taxa_without_data': taxa_without_data.to_dict(orient='records')
	}

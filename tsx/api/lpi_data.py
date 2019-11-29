# -*- coding: UTF-8 -*-
import csv
from flask import request, make_response, g, jsonify, Blueprint, Response
from flask_headers import headers
from tsx.api.util import csv_response
from tsx.db import get_session
from datetime import datetime
from tsx.util import run_parallel, log_time
import tsx.config
import pandas as pd
import os
import json
import numpy as np
import tempfile
import re
from zipfile import ZipFile, ZIP_DEFLATED

bp = Blueprint('lpi_data', __name__)


cached_data = {}
def read_data(filename):
	if filename not in cached_data:
		export_dir = tsx.config.data_dir('export')
		if os.path.isfile(os.path.join(export_dir, filename)):
			# this is going to use quite alot of RAM, but it is more responsive than using dask
			# filename = '/Users/james/tmp/lpi-2018-08-08/lpi-filtered.csv'
			df = pd.read_csv(os.path.join(export_dir, filename), index_col='ID', quoting=csv.QUOTE_MINIMAL, dtype={
				'ID': int,
				'Binomial': str,
				'SpNo': int,
				'TaxonID': str,
				'CommonName': str,
				'Class': str,
				'Order': str,
				'Family': str,
				'FamilyCommonName': str,
				'Genus': str,
				'Species': str,
				'Subspecies': str,
				'FunctionalGroup': str,
				'FunctionalSubGroup': str,
				'EPBCStatus': str,
				'IUCNStatus': str,
				'BirdLifeAustraliaStatus': str,
				'MaxStatus': str,
				'State': str,
				'Region': str,
				'RegionCentroidLatitude': float,
				'RegionCentroidLongitude': float,
				'RegionCentroidAccuracy':float,
				'SiteID': int,
				'SiteDesc': str,
				'SourceID': int,
				'SourceDesc': str,
				'UnitID': int,
				'Unit': str,
				'SearchTypeID': str,
				'SearchTypeDesc': str,
				'ExperimentalDesignType': str,
				'ResponseVariableType': str,
				'DataType': int,
				'TimeSeriesLength': float,
				'TimeSeriesSampleYears': float,
				'TimeSeriesCompleteness': float,
				'TimeSeriesSamplingEvenness': float,
				'NoAbsencesRecorded': str,
				'StandardisationOfMethodEffort': str,
				'ObjectiveOfMonitoring': str,
				'SpatialRepresentativeness': float,
				'SeasonalConsistency': float,
				'ConsistencyOfMonitoring': float,
				'MonitoringFrequencyAndTiming': float,
				'DataAgreement': str,
				'SurveysCentroidLatitude': float,
				'SurveysCentroidLongitude': float,
				'SurveyCount': int,
				'TimeSeriesID': str,
				'NationalPriorityTaxa': int
			})
			# Important: remove sensitive information that must not be exposed publicly
			df = df.drop(['SurveysCentroidLatitude', 'SurveysCentroidLongitude', 'SurveysSpatialAccuracy', 'DataAgreement', 'SiteDesc', 'StatePlantStatus'], axis=1)
			cached_data[filename] = df
		else:
			cached_data[filename] = None

	return cached_data[filename]

# Allows us to switch databases depending on 'dataset' parameter
# For a given dataset, there must be a section in the config file called "database_<dataset name>"
def get_db_session():
	dataset = get_dataset_name()

	if dataset == None:
		return get_session()
	else:
		return get_session(database_config=("database_%s" % dataset))

@bp.route('/lpi-data', methods = ['GET'])
def lpi_data():
	"""Output aggregated data in LPI wide format"""
	#output format: csv or json
	output_format = request.args.get('format', type=str)
	download_file = request.args.get('download', type=str)

	# Filter LPI data based on request parameters
	filtered_dat = get_filtered_data()

	if output_format == None or output_format == 'csv':
		filtered_dat = suppress_aggregated_data(filtered_dat)

		if download_file == None or download_file == "":
			return filtered_dat.to_csv()
		else:
			output = make_response(filtered_dat.to_csv())
			output.headers["Content-Disposition"] = "attachment; filename=%s" % download_file
			output.headers["Content-type"] = "text/csv"
			return output
	elif output_format == 'zip':
		filtered_dat = suppress_aggregated_data(filtered_dat)

		# Create temporary file
		zip_filename = tempfile.mkstemp()[1]

		# Write zip file to temporary file
		with ZipFile(zip_filename, 'w', ZIP_DEFLATED) as zip_file:
			# Write out data
			zip_file.writestr('tsxdata.csv', filtered_dat.to_csv())
			# Write out extra files
			try:
				dataset = get_dataset_name()
				if dataset == None:
					extra_dir = tsx.config.data_dir('download-extras')
				else:
					extra_dir = tsx.config.data_dir('download-extras-%s' % dataset)

				for filename in os.listdir(extra_dir):
					zip_file.write(os.path.join(extra_dir, filename), filename)
			except:
				# Directory may not exist etc. - carry on
				pass

		# A response generator that streams the temporary file and then immediately deletes it
		# TODO - make a utility function "stream_and_delete(path)"
		def generate():
			with open(zip_filename, 'rb') as f:
				while True:
					data = f.read(65536) # 64k chunks
					if not data:
						break
					yield data
			os.remove(zip_filename)

		# Send streaming response + appropriate headers
		return Response(
			generate(),
			mimetype="application/zip",
			headers={
				"Content-Disposition": "attachment; filename=%s" % (download_file or "tsxdata.zip")
			}
		)

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
		return jsonify("Unsupported format (Supported: csv, json, zip)"), 400

@bp.route('/lpi-data/plot', methods = ['GET'])
def plot():
	# Filter data
	df = get_filtered_data()

	return json.dumps({
		'dotplot': get_dotplot_data(df),
		'summary': get_summary_data(df)
	})

@bp.route('/lpi-data/intensity', methods = ['GET'])
@headers({'Cache-Control':'public, max-age=602'})
def get_intensity():
	filtered_data = get_filtered_data()
	if len(filtered_data) == 0:
		return json.dumps([])

	source = request.args.get('source', type=str)
	if source == 'lpi_wide_table':
		"""
		Gets data in format:
		[
			[lat, lon, count], ...
		]
		"""
		dat = filtered_data.to_dict()
		lats = dat['SurveysCentroidLatitude']
		longs = dat['SurveysCentroidLongitude']
		counts = dat['SurveyCount']
		ids = lats.keys()
		return json.dumps([ [lats[id], longs[id], counts[id]] for id in ids ])
	else: # get it from database
		"""
		Gets data in format:
		[
			[lon, lat, [
				[year, count], [year, count], [year, count], ...
			]],
			...
		]
		"""

		enable_consistency_check = False # for testing that DB query and CSV queries match up

		if enable_consistency_check:
			dat = filtered_data.to_dict()
			csv_ids = dat['TimeSeriesID'].values()

		session = get_db_session()

		sql_where_expressions, sql_values = build_filter_sql()

		with log_time("Query database"):
			# Note '.bind' is necessary to run query with positional parameters
			# STRAIGHT_JOIN is necessary to stop MySQL from choosing a very slow query plan
			result = session.bind.execute("""SELECT
							time_series_id,
							start_date_y as Year,
							# 1 as Year, # this is much faster but slightly changes intensity map
							ANY_VALUE(ST_Y(centroid_coords)) as Latitude,
							ANY_VALUE(ST_X(centroid_coords)) as Longitude,
							SUM(survey_count) as Count
							FROM aggregated_by_year
							STRAIGHT_JOIN region ON region.id = aggregated_by_year.region_id
							STRAIGHT_JOIN taxon ON taxon.id = aggregated_by_year.taxon_id
							WHERE include_in_analysis
							AND taxon.taxonomic_group = 'Birds'
							AND %s
							GROUP BY time_series_id, start_date_y""" % sql_where_expressions, sql_values)

		with log_time("Create dataframe"):
			values = pd.DataFrame.from_records(data = result.fetchall(), columns = result.keys())

		if enable_consistency_check:
			csv_ids = set(dat['TimeSeriesID'].values())
			db_ids = set(values['time_series_id'])
			print("CSV: %s time series" % len(csv_ids))
			print("DB:  %s time series" % len(db_ids))

			if csv_ids != db_ids:
				print("csv_ids - db_ids = %s" % (csv_ids - db_ids))
				print("db_ids - csv_ids = %s" % (db_ids - csv_ids))

		session.close()

		with log_time("Reshape data"):
			# Combine year and count into one column
			values['YearCount'] = list(zip(values['Year'], pd.to_numeric(values['Count'])))
			# Group by lat/lon
			result = values.groupby(['Longitude', 'Latitude'])['YearCount'].apply(list).reset_index()

		with log_time("Generate JSON"):
			return json.dumps(result.values.tolist())

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

	# Get only years that have data
	m = df[years].max()
	years = list(m.index[(m.fillna(method='bfill') + m.fillna(method='ffill')).isna() == False])

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

def suppress_aggregated_data(df):
	df = df.copy()

	years = [col for col in df.columns if col.isdigit()]
	df[years] = df[years].multiply(df['SuppressAggregatedData'].apply(lambda x: np.nan if x== 1 else 1), axis="index")

	return df

# Gets 'dataset' request parameter and sanitises it
def get_dataset_name():
	dataset = request.args.get('dataset', type=str)
	if dataset != None:
		dataset = re.sub(r'[^-_\w.]', '', dataset)
	return dataset

def get_unfiltered_data():
	dataset = get_dataset_name()
	if dataset == None:
		return read_data('lpi-filtered.csv')
	else:
		return read_data('lpi-filtered-%s.csv' % dataset)


def get_filtered_data():
	filter_str = build_filter_string()

	df = get_unfiltered_data()

	if filter_str:
		df = df.query(filter_str)
	else:
		df = df.copy()

	# Functional group filtering is a special case because we use a regular expression and can't do this filtering using the 'query' method
	group = request.args.get('group')
	subgroup = request.args.get('subgroup')
	if 'FunctionalSubGroup' in df:
		# Legacy code to support TSX Visualisation until new wide table file is generated
		if group:
			df = df[df.FunctionalGroup == group]
		if subgroup:
			df = df[df.FunctionalSubGroup == subgroup]
	else:
		if group:
			if subgroup:
				regex = "(?:^|,)%s:%s(?:,|$)" % (re.escape(group), re.escape(subgroup))
			else:
				regex = "(?:^|,)%s(?:[:,]|$)" % re.escape(group)

			df = df[df.FunctionalGroup.str.contains(regex)]

	return df


def build_filter_string():
	#spno
	filters = []
	if 'spno' in request.args:
		_sp_no = request.args.get('spno', type=int)
		filters.append("SpNo=='%d'" % (_sp_no))
	if 'datatype' in request.args:
		_sp_no = request.args.get('datatype', type=int)
		filters.append("DataType=='%d'" % (_sp_no))
	#state
	if 'state' in request.args:
		_stateList = request.args.get('state', type=str).split('+')
		filters.append("(%s)" % " or ".join(["State=='%s'" % s for s in _stateList]))
	#searchtypedesc
	if 'searchtype' in request.args:
		_search_type = request.args.get('searchtype', type=int)
		# find in database
		session = get_db_session()
		_search_type_desc = session.execute(
			"""SELECT * FROM search_type WHERE id = :searchtypeid""",
			{'searchtypeid': _search_type}).fetchone()['description']
		filters.append("SearchTypeDesc=='%s'" % (_search_type_desc))
		session.close()
	#subibra
	if 'subibra' in request.args:
		_subibra = request.args.get('subibra', type=str)
		filters.append("SubIBRA=='%s'" % (_subibra))

	#sourceid
	if 'sourceid' in request.args:
		_sourceid = request.args.get('sourceid', type=int)
		filters.append("SourceID=='%d'" % (_sourceid))

	# status/statusauth
	if 'status' in request.args and 'statusauth' in request.args: #IUCN, EPBC, Max
		_statusList = request.args.get('status', type=str).split('+')
		_statusauth = request.args.get('statusauth', type=str)
		filters.append("(%s)" % " or ".join(["%sStatus=='%s'" % (_statusauth, s) for s in _statusList]))

	# national priority
	if 'priority' in request.args:
		filters.append("NationalPriorityTaxa=='%d'" %(request.args.get('priority', type=int)))

	if len(filters) > 0:
		return " and ".join(filters)
	else:
		return None

#SQL version of build_filter_string so that we can filter data directly in the database, which is much faster in certain scenarios
def build_filter_sql(taxon_only=False):
	expressions = []
	values = []

	#spno
	if 'spno' in request.args:
		expressions.append("taxon.spno = %s")
		values.append(request.args.get('spno', type=int))

	# Functional group
	if 'group' in request.args:
		expressions.append("taxon.id IN (SELECT taxon_id FROM taxon_group WHERE group_name = %s)")
		values.append(request.args.get('group', type=str))

	# functional subgroup
	if 'subgroup' in request.args:
		expressions.append("taxon.id IN (SELECT taxon_id FROM taxon_group WHERE subgroup_name = %s)")
		values.append(request.args.get('subgroup', type=str))

	# status/statusauth
	if 'status' in request.args and 'statusauth' in request.args: #IUCN, EPBC, Max
		status_authority = request.args.get('statusauth', type=str).lower()
		statuses = request.args.get('status', type=str).split('+')
		if status_authority in ["uicn", "epbc", "aust", "max"] and len(statuses) > 0:
			expressions.append("taxon.%s_status_id IN (SELECT id FROM taxon_status WHERE description IN (%s))" % (status_authority, in_clause_placeholders(statuses)))
			values.extend(statuses)

	# national priority
	if 'priority' in request.args:
		expressions.append("taxon.national_priority = %s")
		values.append(request.args.get('priority', type=int))

	if not taxon_only:
		# data type
		if 'datatype' in request.args:
			expressions.append("data_type = %s")
			values.append(request.args.get('datatype', type=int))

		#state
		if 'state' in request.args:
			states = request.args.get('state', type=str).split('+')
			expressions.append("region.state IN (%s)" % in_clause_placeholders(states))
			values.extend(states)

		#searchtypedesc
		if 'searchtype' in request.args:
			expressions.append("search_type_id = %s")
			values.append(request.args.get('searchtype', type=int))

		#subibra
		if 'subibra' in request.args:
			expressions.append("region.name = %s")
			values.append(request.args.get('subibra', type=str))

		#sourceid
		if 'sourceid' in request.args:
			expressions.append("source_id = %s")
			values.append(request.args.get('sourceid', type=int))

	if len(expressions):
		return (" AND ".join(expressions), tuple(values))
	else:
		return ("TRUE", ())

def in_clause_placeholders(items):
	return ", ".join(["%s"] * len(items))

@bp.route('/lpi-data/stats', methods = ['GET'])
def stats():
	# Filter data
	df = get_filtered_data()

	return json.dumps(get_stats(df))

@bp.route('/lpi-data/stats.html', methods = ['GET'])
def stats_html():
	# Filter data
	df = get_filtered_data()

	if df.size == 0:
		return "<html><head></head><body><p>No data available</p></body></html>"

	stats = get_stats(df)

	html = u"""
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
						<th>IUCN status</th>
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
		html += u"""
		<tr>
			<td>{common_name}</td>
			<td>{scientific_name}</td>
			<td>{functional_group}</td>
			<td>{iucn_status}</td>
			<td>{epbc_status}</td>
			<td>{num_sources:.0f}</td>
			<td>{num_ts:.0f}</td>
			<td>{ts_length_mean:.1f}</td>
			<td>{spatial_rep:.1f}</td>
		</tr>""".format(**row)

	for row in stats['taxa_without_data']:
		html += u"""
		<tr>
			<td>{common_name}</td>
			<td>{scientific_name}</td>
			<td>{functional_group}</td>
			<td>{iucn_status}</td>
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

	# Get just the relevant taxa

	sql_where_expressions, sql_values = build_filter_sql(taxon_only=True)

	session = get_db_session()
	result = session.bind.execute("""SELECT
			id AS 'TaxonID',
			common_name,
			scientific_name,
			(	SELECT
				GROUP_CONCAT(CONCAT(taxon_group.group_name, COALESCE(CONCAT(' – ', taxon_group.subgroup_name), '')))
				FROM taxon_group
				WHERE taxon_group.taxon_id = taxon.id
			) AS functional_group,
			(SELECT description FROM taxon_status WHERE taxon_status.id = iucn_status_id) AS iucn_status,
			(SELECT description FROM taxon_status WHERE taxon_status.id = epbc_status_id) AS epbc_status
		FROM taxon
		WHERE COALESCE(taxon.max_status_id, 0) NOT IN (0,1,7)
		AND taxon.taxonomic_group = 'Birds'
		AND %s
	""" % sql_where_expressions, sql_values)
	session.close()

	all_taxa = pd.DataFrame.from_records(data = result.fetchall(), index = 'TaxonID', columns = result.keys())

	joined = all_taxa.join(grouped_by_taxon, how='outer').sort_values(['functional_group', 'common_name'], na_position='first')
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

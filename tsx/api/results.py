# -*- coding: UTF-8 -*-
import csv
from flask import request, make_response, g, jsonify, Blueprint, Response
from flask_headers import headers
from tsx.api.util import csv_response
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
from collections import defaultdict
import sqlite3
from functools import lru_cache
import io

bp = Blueprint('results', __name__, url_prefix='/results')

@lru_cache
def read_data(filename, table="time_series", index_col="ID"):
	export_dir = tsx.config.data_dir('export')
	data_path = os.path.join(export_dir, filename)
	if os.path.isfile(data_path):
		db = sqlite3.connect(data_path)
		df = pd.read_sql("SELECT * FROM %s" % table, db, index_col=index_col)
		db.close()
		return df.fillna(value=np.nan)
	else:
		return None

def sanitise_df(df):
	# Important: remove sensitive information that must not be exposed publicly
	df = df.drop(['SurveysCentroidLatitude', 'SurveysCentroidLongitude', 'SurveysSpatialAccuracy', 'DataAgreement', 'SiteDesc', 'SiteName', 'StatePlantStatus'], axis=1, errors='ignore')
	if get_dataset_name() != 'tsx2019':
		df = df.drop(['IntensiveManagement'], axis=1, errors='ignore')

	return df

@bp.route('/time_series', methods = ['GET'])
def download_time_series():
	"""Output aggregated data in LPI wide format"""
	output_format = request.args.get('format', type=str, default='csv')
	download_file = request.args.get('download', type=str)

	# Filter LPI data based on request parameters
	filtered_dat = get_filtered_data()
	filtered_dat = sanitise_df(filtered_dat)
	filtered_dat = suppress_aggregated_data(filtered_dat)
	csv_output = filtered_dat.to_csv()

	if output_format == 'csv':
		output = make_response(csv_output)
		if download_file:
			output.headers["Content-Disposition"] = "attachment; filename=%s" % download_file
			output.headers["Content-type"] = "text/csv"
		return output

	elif output_format == 'zip':
		# Create temporary file
		zip_filename = tempfile.mkstemp()[1]

		# Write zip file to temporary file
		with ZipFile(zip_filename, 'w', ZIP_DEFLATED) as zip_file:
			# Write out data
			filename = request.args.get('data_filename', default='tsxdata.csv', type=str)
			zip_file.writestr(filename, csv_output)
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

		# Send streaming response + appropriate headers
		return Response(
			stream_and_delete(zip_filename),
			mimetype="application/zip",
			headers={
				"Content-Disposition": "attachment; filename=%s" % (download_file or "tsxdata.zip")
			}
		)

	else:
		return jsonify("Unsupported format (Supported: csv, zip)"), 400

# A response generator that streams the temporary file and then immediately deletes it
def stream_and_delete(path):
	with open(path, 'rb') as f:
		while True:
			data = f.read(65536) # 64k chunks
			if not data:
				break
			yield data
	os.remove(path)

@bp.route('/plots', methods = ['GET'])
def plot():
	# Filter data
	df = get_filtered_data()

	return jsonify({
		'dotplot': get_dotplot_data(df),
		'summary': get_summary_data(df, query_type=request.args.get('type', default='all', type=str))
	})

@bp.route('/spatial', methods = ['GET'])
@headers({'Cache-Control':'public, max-age=602'})
def get_intensity():
	filtered_data = get_filtered_data()
	if len(filtered_data) == 0:
		return jsonify([])

	return jsonify(get_intensity_data(filtered_data))


def get_intensity_data(filtered_data, format='json'):
	df = filtered_data
	df = df[['SurveysCentroidLongitude', 'SurveysCentroidLatitude', 'SurveyCount']]
	df = df.groupby(['SurveysCentroidLongitude', 'SurveysCentroidLatitude'], as_index=False).agg('sum')

	if format == 'json':
		return [[round(x[0], 1), round(x[1], 1), x[2]] for x in df.values]
	elif format == 'csv':
		return df.to_csv(index=False)
	else:
		raise ValueError('Invalid format')


def get_dotplot_data(filtered_data, format='json'):
	"""Converts time-series to a minimal form for generating dot plots:
	[
		[[year,count],[year,count] .. ],
		...
	]
	Where count = 0 or 1
	"""
	df = filtered_data

	if len(df) == 0:
		if format == 'json':
			return []
		else:
			return ''

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

	if format == 'json':
		result = []
		for i, row in enumerate(raw_data):
			result.append([[int_years[j], 1 if value > 0 else 0] for j, value in enumerate(row) if value >= 0])

		return result
	elif format == 'csv':
		output = io.StringIO()
		writer = csv.writer(output)
		writer.writerow(['TimeSeries', 'Year', 'NonZeroCount'])
		for i, row in enumerate(raw_data):
			for j, value in enumerate(row):
				if value >= 0:
					writer.writerow([i, int_years[j], 1 if value > 0 else 0])
		return output.getvalue()
	else:
		raise ValueError('Invalid format')

def get_summary_data(filtered_data, format='json', query_type='all'):
	"""Calculates the number of time-series and distinct taxa per year"""
	df = filtered_data

	# Get year columns
	years = [col for col in df.columns if col.isdigit()]
	# Select year columns and fill any gaps in timeseries
	year_df = (df[years].bfill(axis=1) + df[years].ffill(axis=1)).notna()
	# Discard years with no data
	year_df = year_df.loc[:, year_df.any()]

	if format == 'json':
		result = {
			'timeseries': year_df.sum().to_dict()
		}

		if query_type != 'individual':
			result['taxa'] = year_df.groupby(df['TaxonID']).any().sum().to_dict()

		return result
	elif format == 'csv':
		a = year_df.sum()
		b = year_df.groupby(df['TaxonID']).any().sum()
		return (
			pd.concat((a,b),axis=1)
			.reset_index()
			.rename(columns={
				'index':'Year',
				0:'NumberOfTimeSeries',
				1:'NumberOfTaxa'
			})
			.to_csv(index=False)
		)
	else:
		raise ValueError('Invalid format')

def suppress_aggregated_data(df):
	df = df.copy()

	years = [col for col in df.columns if col.isdigit()]
	df[years] = df[years].multiply(df['SuppressAggregatedData'].apply(lambda x: np.nan if (x == '1' or x == 1) else 1), axis="index")

	return df

# Gets 'dataset' request parameter and sanitises it
def get_dataset_name():
	dataset = request.args.get('dataset', type=str)
	if dataset != None:
		dataset = re.sub(r'[^-_\w.]', '', dataset)
	return dataset

def get_database_filename():
	dataset = get_dataset_name()
	if dataset == None:
		return 'results.db'
	else:
		return 'results-%s.db' % dataset

def get_taxon_data():
	return read_data(get_database_filename(), table='taxon', index_col='TaxonID')

def get_trend_data():
	df = read_data(get_database_filename(), table='trend', index_col=None)
	if df['ReferenceYear'].dtype != object:
		df['ReferenceYear'] = df['ReferenceYear'].apply(lambda x: '' if np.isnan(x) else str(int(x)))
	df['has_trend'] = df['TrendData'].notna()
	return df

def get_unfiltered_data():
	return read_data(get_database_filename())

def get_filtered_data():
	params = dict((k, v) for k, v in request.args.items() if v != 'All')
	df = get_unfiltered_data()
	return filter_data(df, params)

def filter_data(df, params):
	df = df.copy()

	# Special logic for threatened *bird* index
	dataset = get_dataset_name()
	if dataset != None and dataset.startswith('tbx'):
		df = df[df['TaxonomicGroup'] == 'Birds']

	# Special logic for individual species
	if params.get('type') == 'individual':
		return df[df['TaxonID'] == params.get('taxon')]

	#taxonomic group
	if 'tgroup' in params:
		df = df[df['TaxonomicGroup'] == params.get('tgroup')]

	#state
	if 'state' in params:
		states = params.get('state').split('+')
		df = df[df['State'].isin(states)]

	# status/statusauth
	if 'status' in params and 'statusauth' in params: #IUCN, EPBC, Max
		statuses = [unabbreviate_status(s) for s in re.split("[_+]", params.get('status'))]
		status_col = params.get('statusauth') + 'Status'
		df = df[df[status_col].isin(statuses)]

	# national priority
	if 'priority' in params:
		df = df[df['NationalPriorityTaxa'] == params.get('priority')]

	if params.get('type') == 'priority':
		df = df[df['NationalPriorityTaxa'] == 1]

	# Functional group
	group = params.get('group')
	subgroup = params.get('subgroup')
	if group:
		if subgroup:
			regex = "(?:^|,)%s:%s(?:,|$)" % (re.escape(group), re.escape(subgroup))
		else:
			regex = "(?:^|,)%s(?:[:,]|$)" % re.escape(group)

		df = df[df.FunctionalGroup.notna() & df.FunctionalGroup.str.contains(regex)]

	# Site management filtering is also special
	management = params.get('management')

	# TODO: Generate new version of these old dataset files so that special cases are not needed
	if get_dataset_name() == 'tsx2019':
		# legacy
		if management == 'No management':
			df = df[df.IntensiveManagement.isna() == True]
		elif management == 'Any management':
			df = df[df.IntensiveManagement.isna() == False]
		elif management == 'Predator-free':
			df = df[df.IntensiveManagementGrouping.str.contains('predator-free', na=False)]
	elif get_dataset_name() == 'tsx2020':
		# also legacy
		if management == "Any management":
			df = df[~(df.IntensiveManagementGrouping.isna() | (df.IntensiveManagementGrouping == "No known management"))]
		elif management == "Predator-free":
			df = df[df.IntensiveManagementGrouping.str.contains('predator-free', na=False)]
		elif management == "Translocation":
			df = df[df.IntensiveManagementGrouping.str.contains('Translocation', na=False)]
		elif management == "No management":
			pass
			df = df[df.IntensiveManagementGrouping.isna() | (df.IntensiveManagementGrouping == "No known management")]
	else:
		if management:
			df = df[df.Management == management]


	return df

def unabbreviate_status(status):
	return {
		'NT': 'Near Threatened',
		'VU': 'Vulnerable',
		'EN': 'Endangered',
		'CR': 'Critically Endangered'
	}.get(status, status)


@bp.route('/stats.html', methods = ['GET'])
def stats_html():
	# Filter data
	df = get_filtered_data()

	if df.size == 0:
		return "<html><head></head><body><p>No data available</p></body></html>"

	stats = get_stats(df)

	query_type = request.args.get('type', default='all', type=str)

	include_spatial_rep = get_dataset_name() != 'tsx2023'

	template = u"""
	<html>
		<head>
	"""

	if not include_spatial_rep:
		template += "<style>.spatial_rep {{ display: none; }}</style>"

	template += u"""
		</head>
		<body>
			<p>
				Number of time series in Index: {num_ts}
			</p>
			<p>
				Time series length (mean ± SD): {ts_length_mean:.1f} ± {ts_length_stddev:.1f}
			</p>
			<p>
				Number of samples (years) per time series (mean ± SD): {ts_years_mean:.1f} ± {ts_years_stddev:.1f}
			</p>"""

	if query_type != "individual":
		template += u"""
			<p>
				Number of data sources in Index: {num_sources}
			</p>
			<p>
				Number of taxa in Index: {num_taxa}
			</p>
		"""
	else:
		template += u"""
			<p>
				Number of data sources: {num_sources}
			</p>
		"""

	template += u"""
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
						<th class='spatial_rep'>Spatial representativeness</th>
					</tr>
				</thead>
				<tbody>
	"""

	html = template.format(**stats)

	for row in stats['taxa']:
		html += """
		<tr>
			<td>{CommonName}</td>
			<td>{ScientificName}</td>
			<td>{FunctionalGroup}</td>
			<td>{IUCNStatus}</td>
			<td>{EPBCStatus}</td>
			<td>{num_sources:.0f}</td>
			<td>{num_ts:.0f}</td>
			<td>{ts_length_mean:.1f}</td>
			<td class='spatial_rep'>{spatial_rep:.1f}</td>
		</tr>""".format(**row).replace(">nan<", ">-<")

	html += """
				</tbody>
			</table>
		</body>
	</html>
	"""

	return html

def get_filtered_taxa():
	taxa = get_taxon_data()

	taxa_params = {}
	for key in ['tgroup', 'group', 'subgroup', 'status', 'statusauth', 'priority']:
		value = request.args.get(key, default='All', type=str)
		if value != 'All':
			taxa_params[key] = value

	taxa = filter_data(taxa, taxa_params)
	return taxa

def get_stats(filtered_data):
	df = filtered_data

	grouped_by_taxon = df.groupby(['TaxonID']).agg({
		'TimeSeriesLength': np.mean,
		'SourceDesc': 'nunique',
		'TimeSeriesID': 'nunique',
		'SpatialRepresentativeness': np.mean,
	}).rename(columns = {
		'TimeSeriesLength': 'ts_length_mean',
		'SourceDesc': 'num_sources',
		'TimeSeriesID': 'num_ts',
		'SpatialRepresentativeness': 'spatial_rep'
	})

	taxa = get_filtered_taxa()

	if 'taxon' in request.args:
		taxa = taxa[taxa.index == request.args.get('taxon', type=str)]

	taxa = taxa.join(grouped_by_taxon, how='outer')
	taxa['no_data'] = taxa['num_ts'].isna()
	taxa = taxa.sort_values(['no_data', 'FunctionalGroup', 'CommonName'], na_position='first')
	taxa = taxa.reset_index().rename(columns = { 'TaxonID': 'taxon_id' })

	return {
		'num_sources': df['SourceDesc'].nunique(),
		'num_taxa': df['TaxonID'].nunique(),
		'num_ts': len(df),
		'ts_length_mean': df['TimeSeriesLength'].mean(),
		'ts_length_stddev': df['TimeSeriesLength'].std(),
		'ts_years_mean': df['TimeSeriesSampleYears'].mean(),
		'ts_years_stddev': df['TimeSeriesSampleYears'].std(),
		'taxa': taxa.to_dict(orient='records')
	}

def get_filtered_trends(params):
	return get_filtered_trends_cached(tuple(params.items()))

def get_options(name, params):
	params = tuple(item for item in params.items() if item[0] != name)
	return get_options_cached(name, params)

# @cache
def get_filtered_trends_cached(params):
	df = get_trend_data()
	df = df.assign(**{
		'included': True,
	})
	for key, value in params:
		df['included'] = df['included'] & (df[key] == value)

	df['has_trend'] = df['included'] & df['has_trend']
	return df

# @cache
def get_options_cached(name, params):
	df = get_filtered_trends_cached(params)
	param_dict = dict(params)

	# Ignore trends where this parameter is not set
	df = df[df[name].notna()]

	# Functional group parameters are special: we only show valid combinations of TaxonomicGroup/FunctionalGroup/FunctionSubGroup (irrespective of other filtering parameters)
	if name == 'FunctionalGroup':
		df = df[df['TaxonomicGroup'] == param_dict['TaxonomicGroup']]
	elif name == 'FunctionalSubGroup':
		df = df[df['TaxonomicGroup'] == param_dict['TaxonomicGroup']]
		df = df[df['FunctionalGroup'] == param_dict['FunctionalGroup']]

	df = df[[name, 'included', 'has_trend']].groupby(name).agg({ 'included': 'any', 'has_trend': 'any' }).reset_index()

	# Special case for individual species
	if 'TaxonID' in param_dict and name in ['TaxonomicGroup', 'FunctionalGroup']:
		df['included'] = True
		df['has_trend'] = True

	df = df[df['included'] & df['has_trend']]

	options = [{
		'label': option_label(row[name], name, row['included'], row['has_trend']),
		'value': row[name],
		'disabled': option_disabled(row[name], name, row['included'], row['has_trend'])
	} for row in (row._asdict() for row in df.itertuples())]

	if name == 'StatusAuthority' and param_dict['TaxonomicGroup'] not in ['Birds', 'All']:
		options = [x for x in options if x['value'] != 'BirdActionPlan']

	# Make default option first
	options = sorted(options, key=lambda o: o['label'] not in ['All', 'All sites'])

	# Special case - remove 'All' status for EPBC
	if name == 'Status' and param_dict['StatusAuthority'] == 'EPBC':
		options = [x for x in options if x['value'] != 'NT_VU_EN_CR']

	return options

def get_parameter_values():
	# Note: ReferenceYear is not included here because it is treated specially

	query_type = request.args.get('type', default='all', type=str)

	if query_type == 'all':
		return {
			'TaxonomicGroup': 		request.args.get('tgroup', default='All', type=str),
			'FunctionalGroup': 		request.args.get('group', default='All', type=str),
			'FunctionalSubGroup': 	request.args.get('subgroup', default='All', type=str),
			'State': 				request.args.get('state', default='All', type=str),
			'StatusAuthority': 		request.args.get('statusauth', default='Max', type=str),
			'Status': 				request.args.get('status', default='NT_VU_EN_CR', type=str),
			'Management': 			request.args.get('management', default='All', type=str)
		}
	elif query_type == 'priority':
		return {
			'TaxonomicGroup': 		request.args.get('tgroup', default='All', type=str),
			'FunctionalGroup': 		request.args.get('group', default='All', type=str),
			'State': 				request.args.get('state', default='All', type=str),
			'Management': 			request.args.get('management', default='All', type=str),
			'NationalPriorityTaxa': '1'
		}
	else:
		return {
			'TaxonID':				request.args.get('taxon', default=None, type=str)
		}

def option_disabled(value, param, has_data, has_trend):
	if param == 'ReferenceYear':
		return not has_trend
	else:
		return not has_data

def option_label(value, param, has_data, has_trend):
	if param == 'ReferenceYear':
		return value
	elif param == 'Status':
		label = {
			'VU_EN_CR': 'Threatened species (all Vulnerable + Endangered + Critically Endangered)',
			'NT_VU_EN_CR': 'All (all Near Threatened + Vulnerable + Endangered + Critically Endangered)',
			'NT': 'Near Threatened species (Near Threatened species only)'
		}.get(value)
	elif param == 'StatusAuthority':
		label = {
			'Max': 'Max',
			'EPBC': 'EPBC',
			'IUCN': 'Australian IUCN status',
			'BirdActionPlan': '2020 Bird Action Plan'
		}.get(value)
	elif param == 'Management' and value == 'All':
		return 'All sites'
	else:
		label = value

	if label:
		if not has_data:
			label += " (No data)"
		elif not has_trend:
			label += " (No trend possible)"

	return label


def get_taxon_options(param_values):
	# Get just the taxa that meet current filters
	taxa = get_filtered_taxa()[['CommonName', 'ScientificName']]

	# Get all individual taxa trends
	trends = get_trend_data()
	trends = trends[trends["TaxonID"].notna()]
	trends = trends.groupby('TaxonID').agg({'has_trend':'any'})

	df = taxa.join(trends, how='inner').reset_index()

	options = [get_taxon_option(*row) for row in df.itertuples(index=False)]

	default_option = {
		'label': 'Select…',
		'value': None
	}

	return [default_option] + sorted(options, key=lambda x: x['label'])

def get_taxon_option(taxon_id, common_name, scientific_name, has_trend):
	if common_name and pd.notna(common_name):
		label = "%s (%s)" % (common_name, scientific_name)
	else:
		label = scientific_name

	if not has_trend:
		label = label + " (No trend possible)"

	return {
		'label': label,
		'value': taxon_id
	}

@bp.route('/params', methods = ['GET'])
def get_parameters():
	df = get_trend_data()
	param_values = get_parameter_values()

	query_type = request.args.get('type', default='all', type=str)

	if query_type in ['all', 'priority']:
		# Special logic for reference year: try to maintain current reference year, but if there is no trend for that year, switch to the earliest year that has a trend (if any)
		reference_year = request.args.get('refyear', default='1985', type=str)
		reference_year_options = get_options('ReferenceYear', param_values)
		ok_reference_years = [opt['value'] for opt in reference_year_options if not opt['disabled']]
		if reference_year not in ok_reference_years and len(ok_reference_years) > 0:
			reference_year = ok_reference_years[0]

	if query_type == 'all':
		# Special case - remove 'All' status for EPBC
		if param_values['Status'] == 'NT_VU_EN_CR' and param_values['StatusAuthority'] == 'EPBC':
			param_values['Status'] = 'VU_EN_CR'

	results = {}

	params = [
		dict(name='type',
			type='radio',
			options=[dict(label='All Species', value='all'),
					 dict(label='Priority Species', value='priority'),
					 dict(label='Individual species', value='individual')],
			value=query_type)]

	if query_type == 'all':
		params += [
			dict(name='tgroup',
				label='Index',
				type='select',
				options=get_options('TaxonomicGroup', param_values),
				value = param_values['TaxonomicGroup']),
			dict(name='group',
				label='Group',
				type='select',
				options=get_options('FunctionalGroup', param_values),
				value = param_values['FunctionalGroup']),
			dict(name='subgroup',
				label='Sub-group',
				type='select',
				options=get_options('FunctionalSubGroup', param_values),
				disabled=len(get_options('FunctionalSubGroup', param_values)) == 1,
				value=param_values['FunctionalSubGroup']),
			dict(name='state',
				label='State / Territory',
				type='select',
				options=get_options('State', param_values),
				value=param_values['State']),
			dict(name='statusauth',
				label='Status authority',
				type='select',
				options=get_options('StatusAuthority', param_values),
				value=param_values['StatusAuthority']),
			dict(name='status',
				label='Status',
				type='select',
				options=get_options('Status', param_values),
				value=param_values['Status']),
			dict(name='management',
				label='Management',
				type='select',
				options=get_options('Management', param_values),
				value=param_values['Management']),
			dict(name='refyear',
				label='Reference year',
				type='button-radio',
				options=reference_year_options,
				value=reference_year)
		]

	elif query_type == 'priority':
		params += [
			dict(name='tgroup',
					label='Index',
					type='select',
					options=get_options('TaxonomicGroup', param_values),
					value = param_values['TaxonomicGroup']),
			dict(name='group',
				label='Group',
				type='select',
				options=get_options('FunctionalGroup', param_values),
				value = param_values['FunctionalGroup']),
			dict(name='state',
				label='State / Territory',
				type='select',
				options=get_options('State', param_values),
				value=param_values['State']),
			dict(name='management',
				label='Management',
				type='select',
				options=get_options('Management', param_values),
				value=param_values['Management']),
			dict(name='refyear',
				label='Reference year',
				type='button-radio',
				options=reference_year_options,
				value=reference_year)
		]

	elif query_type == 'individual':
		tgroup = request.args.get('tgroup', type=str, default='All')
		group = request.args.get('group', type=str, default='All')

		taxon_id = param_values['TaxonID']
		taxon_options = get_taxon_options(param_values)
		group_options = get_options('FunctionalGroup', {
					'TaxonomicGroup': tgroup, 'TaxonID': None })

		if taxon_id and taxon_id not in [option['value'] for option in taxon_options]:
			taxon_id = None

		if group and group not in [option['value'] for option in group_options]:
			group = 'All'

		params += [
			dict(name='tgroup',
				label='Index',
				type='select',
				options=get_options('TaxonomicGroup', {}),
				value = tgroup),
			dict(name='group',
				label='Group',
				type='select',
				options=group_options,
				value = group),
			dict(name='taxon',
				label='Available Species',
				type='searchable-select',
				options=taxon_options,
				value=taxon_id)
		]
	else:
		return jsonify('Invalid type (must be one of: all, priority, individual)'), 400

	data_params = { p['name']: p['value'] for p in params }
	data_params['dataset'] = get_dataset_name()

	if query_type == 'individual':
		data_params.pop('tgroup', None)
		data_params.pop('group', None)


	return jsonify({
		'fields': params,
		'data_params': data_params
	})

def parse_trend(trend):
	result = []

	for line in trend.split("\n"):
		values = [ x.strip('"') for x in line.split(" ") ]

		if len(values) == 4 and values[0].isnumeric() and values[2] != 'NA':
			result.append([int(values[0]), float(values[1]), float(values[2]), float(values[3])])

	return dict(zip(['year', 'value', 'low', 'high'], list(zip(*result)))) # Column-wise


@bp.route('/trends', methods = ['GET'])
def get_trend():
	if request.args.get('type', default='all', type=str) == 'individual':
		param_values = {
			'TaxonID': request.args.get("taxon", type=str, default=None)
		}
	else:
		param_values = get_parameter_values()
		param_values['ReferenceYear'] = request.args.get('refyear', default='1985', type=str)

	df = get_filtered_trends(param_values)

	df = df[df['included']]

	if len(df) > 1:
		return jsonify("Parameters do not uniquely identify a permutation [%s permutations found]" % len(df)), 400

	if len(df) == 0:
		return jsonify("No data found"), 404

	trend_data = df['TrendData'].dropna()

	if len(trend_data) == 0:
		return jsonify("No trend found"), 404

	raw_trend = trend_data.values[0]

	result_format = request.args.get('format', default='json', type=str)

	if result_format == 'raw':
		return raw_trend
	elif result_format == 'json':
		return jsonify(parse_trend(raw_trend))
	elif result_format == 'csv':
		t = parse_trend(raw_trend)
		output = io.StringIO()
		writer = csv.writer(output)
		writer.writerow(t.keys())
		writer.writerows(zip(*t.values()))
		return Response(output.getvalue(), mimetype="text/csv")
	else:
		return jsonify("Invalid format (Allowed formats: raw, json)"), 400

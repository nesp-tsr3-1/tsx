from flask import Blueprint
from flask import Blueprint, jsonify, request, send_file, session, Response
from tsx.api.util import db_session, get_user, get_roles, jsonify_rows
from tsx.util import Bunch
from tsx.api.validation import *
from tsx.api.permissions import permitted
from sqlalchemy import text
from tsx.api import subset
import json
import pandas as pd
import math
import dataclasses
from tsx.api.custodian_feedback_pdf import generate_pdf
from tsx.api.custodian_feedback_shared import *

bp = Blueprint('custodian_feedback', __name__)

@bp.route('/custodian_feedback/taxon_datasets', methods = ['GET'])
def taxon_datasets():
	user = get_user()

	if not permitted(user, 'list', 'custodian_feedback_dataset'):
		return "Not authorized", 401

	rows = db_session.execute(text("""
		WITH taxon_dataset AS (
			SELECT
				source_id,
				taxon_id,
				dataset_id,
				MAX(custodian_feedback.id * (feedback_type.code = 'integrated')) AS last_integrated_id,
				MAX(custodian_feedback.id * (feedback_type.code = 'admin')) AS admin_id
			FROM custodian_feedback
			JOIN feedback_type ON feedback_type.id = custodian_feedback.feedback_type_id
			GROUP BY source_id, taxon_id
		),
		json_items AS (
			SELECT JSON_OBJECT(
				'source', JSON_OBJECT(
					'id', source.id,
					'description', source.description
				),
				'taxon', JSON_OBJECT(
					'id', taxon.id,
					'scientific_name', taxon.scientific_name
				),
				'id', CONCAT(source.id, '_', taxon.id),
				'integrated_feedback_status', JSON_OBJECT(
					'code', integrated_status.code,
					'description', integrated_status.description
				),
				'time_created', DATE_FORMAT(integrated.time_created, "%Y-%m-%d %H:%i:%sZ"),
				'last_modified', DATE_FORMAT(integrated.last_modified, "%Y-%m-%d %H:%i:%sZ"),
				'admin_feedback_status', JSON_OBJECT(
					'code', admin_status.code,
					'description', admin_status.description
				)
			) AS item
			FROM taxon_dataset
			JOIN custodian_feedback integrated ON integrated.id = taxon_dataset.last_integrated_id
			JOIN feedback_status integrated_status ON integrated_status.id = integrated.feedback_status_id
			JOIN source ON integrated.source_id = source.id
			JOIN taxon ON integrated.taxon_id = taxon.id
			LEFT JOIN custodian_feedback admin ON admin.id = taxon_dataset.admin_id
			LEFT JOIN feedback_status admin_status ON admin_status.id = admin.feedback_status_id
		)
		SELECT JSON_ARRAYAGG(item) FROM json_items
	"""))

	[(result,)] = rows
	return Response(result, mimetype='application/json')

@bp.route('/custodian_feedback/taxon_datasets/<data_id>', methods = ['GET'])
def taxon_dataset(data_id):
	user = get_user()

	if not permitted(user, 'view', 'custodian_feedback_dataset', data_id):
		return "Not authorized", 401

	can_view_admin_forms = permitted(user, 'view', 'custodian_feedback_admin_forms', data_id)

	try:
		(source_id, taxon_id) = data_id.split('_', 1)
	except ValueError:
		return "Not found", 404

	rows = db_session.execute(text("""
		WITH forms AS (
			SELECT JSON_OBJECT(
				'id', custodian_feedback.id,
				'feedback_type', JSON_OBJECT(
					'code', feedback_type.code,
					'description', feedback_type.description
				),
				'feedback_status', JSON_OBJECT(
					'code', feedback_status.code,
					'description', feedback_status.description
				),
				'time_created', DATE_FORMAT(custodian_feedback.time_created, "%Y-%m-%d %H:%i:%sZ"),
				'last_modified', DATE_FORMAT(custodian_feedback.last_modified, "%Y-%m-%d %H:%i:%sZ")
			) AS form
			FROM custodian_feedback
			JOIN feedback_status ON feedback_status.id = custodian_feedback.feedback_status_id
			JOIN feedback_type ON feedback_type.id = custodian_feedback.feedback_type_id
			WHERE custodian_feedback.dataset_id = :data_id
			AND (:can_view_admin_forms OR feedback_type.code != 'admin')
			ORDER BY custodian_feedback.last_modified DESC
		)
		SELECT JSON_OBJECT(
			'id', :data_id,
			'forms', (SELECT JSON_ARRAYAGG(form) FROM forms),
			'source', JSON_OBJECT(
				'id', source.id,
				'description', source.description
			),
			'taxon', JSON_OBJECT(
				'id', taxon.id,
				'scientific_name', taxon.scientific_name
			)
		)
		FROM source, taxon
		WHERE source.id = :source_id
		AND taxon.id = :taxon_id
	"""), {
		'data_id': data_id,
		'source_id': source_id,
		'taxon_id': taxon_id,
		'can_view_admin_forms': can_view_admin_forms
	})

	rows = list(rows)
	if not rows:
		return "Not found", 404

	[(result,)] = rows
	return Response(result, mimetype='application/json')

def field_json(field):
	return {
		"name": field.name,
		"title": field.title,
		"type": field.type
	}

@bp.route('/custodian_feedback/form_definition', methods = ['GET'])
def form_definition():
	json = {
		"options": field_options,
		"fields": [field_json(field) for field in form_fields]
	}
	return jsonify(json)


@bp.route('/custodian_feedback/forms/<form_id>', methods = ['GET'])
def form(form_id):
	user = get_user()

	if not permitted(user, 'view', 'custodian_feedback_form', form_id):
		return "Not authorized", 401

	form_json = get_form_json_raw(form_id)

	if not form_json:
		return "Not found", 404

	return Response(form_json, mimetype='application/json')

@bp.route('/custodian_feedback/forms/<form_id>/pdf', methods = ['GET'])
def form_pdf(form_id):
	user = get_user()

	if not permitted(user, 'view', 'custodian_feedback_form', form_id):
		return "Not authorized", 401

	pdf = generate_pdf(form_id)

	return Response(pdf,
		mimetype='application/pdf',
		headers={
			"Content-Disposition": "attachment; filename=TSX_Custodian_Feedback_%s.pdf" % form_id
		})

def db_insert(table, row_dict):
	keys, values = zip(*row_dict.items())

	for key in [*keys, table]:
		if not key.isidentifier():
			raise ValueError("%s is not a supported identifier" % key)

	cols = ", ".join("`%s`" % key for key in keys)
	placeholders = ", ".join(":%s" % key for key in keys)
	sql = "INSERT INTO `%s` (%s) VALUES (%s)" % (table, cols, placeholders)

	db_session.execute(text(sql), row_dict)

def parse_field(raw_value, field):
	if raw_value is None:
		return None
	if field.type == 'any':
		return raw_value
	elif field.type == 'str':
		return str(raw_value)
	elif field.type == 'int':
		try:
			return int(raw_value)
		except ValueError:
			return None
	elif field.type == 'options':
		return raw_value
	else:
		print("Unknown field type: %s" % field)
		return raw_value

def parse_fields(raw_json, fields):
	result = {}

	for field in fields:
		if field.name in raw_json:
			result[field.name] = parse_field(raw_json[field.name], field)

	return result

def feedback_type_code(form_id):
	rows = db_session.execute(text("""
		SELECT feedback_type.code
		FROM custodian_feedback, feedback_type
		WHERE custodian_feedback.feedback_type_id = feedback_type.id
		AND custodian_feedback.id = :form_id
	"""), {
		'form_id': form_id
	}).fetchall()

	if len(rows):
		[(code,)] = rows
		return code
	else:
		return None

@bp.route('/custodian_feedback/forms/<form_id>', methods = ['PUT'])
def update_form(form_id):
	user = get_user()

	if not permitted(user, 'update', 'custodian_feedback_form', form_id):
		return "Not authorized", 401

	context = Bunch()
	context.submitting = (request.json.get('action') == 'submit')
	context.feedback_type = feedback_type_code(form_id)

	errors = validate_fields(form_fields, request.json, context)
	if len(errors):
		return jsonify(errors), 400

	field_data = parse_fields(request.json, form_fields)

	db_session.execute(text("""
		DELETE FROM custodian_feedback_answers WHERE custodian_feedback_id = :form_id
		"""), { 'form_id': form_id })

	db_insert('custodian_feedback_answers', {
		'custodian_feedback_id': form_id,
		**field_data
	})

	if context.submitting:
		new_status_code = 'complete'
	else:
		new_status_code = 'draft'

	db_session.execute(text("""
		UPDATE custodian_feedback
		SET feedback_status_id = (SELECT id FROM feedback_status WHERE code = :new_status_code)
		WHERE id = :form_id
	"""), { 'form_id': form_id, 'new_status_code': new_status_code })

	db_session.commit()

	return "OK", 200

# TODO: Trigger updating of dataset stats automatically as required
@bp.route('/custodian_feedback/update_dataset_stats', methods = ['GET'])
def update_dataset_stats_all():
	user = get_user()

	if not permitted(user, 'generate', 'dataset_stats'):
		return "Not authorized", 401

	while True:
		# Find a dataset that needs updating
		rows = db_session.execute(text("""
			SELECT DISTINCT t1_survey.source_id, t1_sighting.taxon_id, t1_survey.data_import_id
			FROM t1_survey, t1_sighting
			WHERE t1_sighting.survey_id = t1_survey.id
			AND data_import_id IS NOT NULL
			AND (t1_survey.source_id, t1_sighting.taxon_id, t1_survey.data_import_id) NOT IN (select source_id, taxon_id, data_import_id FROM dataset_stats)
			LIMIT 1;
			"""))

		rows = list(rows)

		if rows:
			[(source_id, taxon_id, data_import_id)] = rows
			update_dataset_stats(source_id, taxon_id, data_import_id)
		else:
			return 'OK', 200


def processing_summary(source_id, taxon_id):
	result = db_session.execute(text("""
		SELECT DISTINCT
			search_type.description AS search_type,
			unit.description AS unit,
			unit_type.description AS unit_type
		FROM
			t1_survey
			JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
			JOIN t1_site ON t1_survey.site_id = t1_site.id
			JOIN search_type ON t1_site.search_type_id = search_type.id
			JOIN unit ON t1_sighting.unit_id = unit.id
			LEFT JOIN unit_type ON unit.unit_type_id = unit_type.id
		WHERE
			t1_survey.source_id = :source_id
			AND t1_sighting.taxon_id = :taxon_id
		"""), {
		'source_id': source_id,
		'taxon_id': taxon_id
	})

	return [dict(row._mapping) for row in result]

def site_management_summary(source_id, taxon_id):
	result = db_session.execute(text("""
		SELECT
			management.description AS management_category,
			t1_site.management_comments,
			COUNT(DISTINCT t1_site.id) AS site_count
		FROM
			t1_survey
			JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
			JOIN t1_site ON t1_survey.site_id = t1_site.id
			JOIN management ON t1_site.management_id = management.id
		WHERE
			t1_survey.source_id = :source_id
			AND t1_sighting.taxon_id = :taxon_id
		GROUP BY
			management_category, management_comments
		"""), {
		'source_id': source_id,
		'taxon_id': taxon_id
	})

	return [dict(row._mapping) for row in result]

def raw_data_stats(source_id, taxon_id):
	result = db_session.execute(text("""
		SELECT JSON_OBJECT(
			'min_year', MIN(t1_survey.start_date_y),
			'max_year', MAX(t1_survey.start_date_y),
			'survey_count', COUNT(DISTINCT t1_survey.id),
			'min_count', MIN(t1_sighting.`count`),
			'max_count', MAX(t1_sighting.`count`),
			'zero_counts', SUM(t1_sighting.`count` = 0)
		) AS json
		FROM
			t1_survey
			JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
		WHERE
			t1_survey.source_id = :source_id
			AND t1_sighting.taxon_id = :taxon_id
		"""), {
		'source_id': source_id,
		'taxon_id': taxon_id
	})

	[(json_result,)] = result

	return json.loads(json_result)

def time_series_stats(lpi_path):
	df = pd.read_csv(lpi_path)

	year_cols = [col for col in df.columns if col.isdigit()]
	gaps = (
		# Un-pivot to ID,year,value
		df.melt(id_vars=['ID'], value_vars=year_cols, var_name='year')
			# Remove years without values
			.loc[lambda df: df.value.notna()]
			.drop(columns=['value'])
			# Calculate consecutive differences between years
			.sort_values(by=['ID', 'year'])
			.assign(year=lambda df:pd.to_numeric(df.year))
			.assign(year_diff = lambda df:df.year.diff() - 1)
			# Only retain gaps of 1 year or more
			.loc[lambda df: (df.ID.diff() == 0) & (df.year_diff > 0)]
	)
	evenness = gaps[['ID', 'year_diff']].groupby('ID').var().year_diff

	return {
		'time_series_count': len(df),
		'time_series_length_mean': safe_float(df.TimeSeriesLength.mean()),
		'time_series_length_std': safe_float(df.TimeSeriesLength.std()),
		'time_series_sample_years_mean': safe_float(df.TimeSeriesSampleYears.mean()),
		'time_series_sample_years_std': safe_float(df.TimeSeriesSampleYears.std()),
		'time_series_completeness_mean': safe_float(df.TimeSeriesCompleteness.mean() * 100),
		'time_series_completeness_std': safe_float(df.TimeSeriesCompleteness.std() * 100),
		'time_series_sampling_evenness_mean': safe_float(evenness.mean()),
		'time_series_sampling_evenness_std': safe_float(evenness.std())
	}

def safe_float(x):
	x = float(x)
	if math.isnan(x):
		return 0
	else:
		return x

def update_dataset_stats(source_id, taxon_id, data_import_id):
	subset_params = {
		'source_id': source_id,
		'taxon_id': taxon_id
	}

	trend_path, lpi_path = subset.subset_generate_trend_sync(subset_params)

	try:
		with open(trend_path, 'r') as file:
			trend_data = file.read()
	except:
		trend_data = None

	# Generate monitoring consistency plot
	stats = {
		'monitoring_consistency': subset.monitoring_consistency_plot_json(subset_params),
		'intensity_map': subset.subset_intensity_map_json(subset_params),
		'time_series_stats': time_series_stats(lpi_path),
		'raw_data_stats': raw_data_stats(source_id, taxon_id),
		'trend': trend_data,
		'processing_summary': processing_summary(source_id, taxon_id),
		'site_management_summary': site_management_summary(source_id, taxon_id)
	}
	db_insert('dataset_stats', {
		'source_id': source_id,
		'taxon_id': taxon_id,
		'data_import_id': data_import_id,
		'stats_json': json.dumps(stats)
	})
	db_session.commit()


@bp.route('/custodian_feedback/consent', methods = ['GET'])
def get_consent():
	user = get_user()

	if not user:
		return "Not authorized", 401

	result = db_session.execute(text("""
		SELECT consent_given, consent_name
		FROM custodian_feedback_consent
		WHERE user_id = :user_id
	"""), {
		'user_id': user.id
	}).fetchall()

	if len(result):
		result = dict(result[0]._mapping)
		result['consent_given'] = bool(result['consent_given'])
		return jsonify(result)
	else:
		return jsonify({})

@bp.route('/custodian_feedback/consent', methods = ['PUT'])
def update_consent():
	user = get_user()

	if not user:
		return "Not authorized", 401

	consent_given = request.json['consent_given']
	consent_name = request.json['consent_name']

	db_session.execute(text("""
		DELETE FROM custodian_feedback_consent WHERE user_id = :user_id
		"""), {
		'user_id': user.id
	})
	db_session.execute(text("""
		INSERT INTO custodian_feedback_consent (user_id, consent_given, consent_name)
		VALUES (:user_id, :consent_given, :consent_name)
		"""), {
		'user_id': user.id,
		'consent_given': consent_given,
		'consent_name': consent_name
	})
	db_session.commit()

	return "OK", 200

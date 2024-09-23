from tsx.api.util import db_session, db_insert
from tsx.api.validation import *
from sqlalchemy import text
from tsx.api import subset
import json
import pandas as pd
import math
import logging

log = logging.getLogger(__name__)

val_yn = validate_one_of('yes', 'no')
val_ynu = validate_one_of('yes', 'no', 'unsure')

field_options = {
	"standardisation_of_method_effort": [
	{
		"id": 6,
		"description": "Pre-defined sites/plots surveyed repeatedly through time using a single standardised method and effort across the whole monitoring program"
	},
	{
		"id": 5,
		"description": "Pre-defined sites/plots surveyed repeatedly through time with methods and effort standardised within site units, but not across program - i.e. different sites surveyed have different survey effort/methods"
	},
	{
		"id": 4,
		"description": "Pre-defined sites/plots surveyed repeatedly through time with varying methods and effort"
	},
	{
		"id": 3,
		"description": "Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping possible - e.g. a lot of fixed area/time searches conducted within a region but not at pre-defined sites"
	},
	{
		"id": 2,
		"description": "Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping not possible"
	},
	{
		"id": 1,
		"description": "Unstandardised methods/effort, surveys not site-based"
	}
	],
	"objective_of_monitoring": [
	{
		"id": 4,
		"description": "Monitoring for targeted conservation management"
	},
	{
		"id": 3,
		"description": "Monitoring for general conservation management – ‘surveillance’ monitoring"
	},
	{
		"id": 2,
		"description": "Baseline monitoring"
	},
	{
		"id": 1,
		"description": "Monitoring for community engagement"
	},
	{
		"id": "NA",
		"description": "Not defined"
	}
	],
	"consistency_of_monitoring": [
	{
		"id": 4,
		"description": "Balanced; all (or virtually all) sites surveyed in each year sampled (no, or virtually no, site turnover)"
	},
	{
		"id": 3,
		"description": "Imbalanced (low turnover); sites surveyed consistently through time as established, but new sites are added to program with time."
	},
	{
		"id": 2,
		"description": "Imbalanced (high turnover); new sites are surveyed with time, but monitoring of older sites is often not always maintained."
	},
	{
		"id": 1,
		"description": "Highly Imbalanced (very high turnover); different sites surveyed in different sampling periods. Sites are generally not surveyed consistently through time (highly biased)"
	}
	],
	"monitoring_frequency_and_timing": [
	{
		"id": 3,
		"description": "Monitoring frequency and timing appropriate for taxon"
	},
	{
		"id": 2,
		"description": "Monitoring frequency or timing inappropriate for taxon for majority of data."
	},
	{
		"id": 1,
		"description": "Monitoring ad-hoc; no pattern to surveys for majority of data (incidental)"
	}
	],
	"absences_recorded": [
	{
		"id": "yes",
		"description": "Yes"
	},
	{
		"id": "no",
		"description": "No"
	},
	{
		"id": "partially",
		"description": "Partially (for some of the survey period)"
	}
	],
	"monitoring_program_information_provided": [
	{
		"id": "provided",
		"description": "I will provide answers to questions 17 to 32 in this feedback form."
	},
	{
		"id": "provided_copy",
		"description": "I have already provided answers to questions 17 to 32 in a separate feedback form. Please copy them across."
	},
	{
		"id": "please_contact",
		"description": "I prefer to be contacted by phone or video call to answer questions 17 to 32"
	},
	{
		"id": "not_provided",
		"description": "I will not be providing answers to questions 17 to 32"
	}
	],
	"yes_no": [
	{
		"id": "yes",
		"description": "Yes"
	},
	{
		"id": "no",
		"description": "No"
	}
	],
	"yes_no_unsure": [
	{
		"id": "yes",
		"description": "Yes"
	},
	{
		"id": "no",
		"description": "No"
	},
	{
		"id": "unsure",
		"description": "Unsure"
	}
	],
	"admin_type": [
	{
		"id": "formal",
		"description" : "Formal"
	},
	{
		"id": "informal",
		"description": "Informal"
	}
	]
}

def val_required_for_submit(value, field, context):
	if context.submitting:
		return validate_required(value, field, context)

def val_required_integrated_only(value, field, context):
	if context.submitting and context.feedback_type == 'integrated':
		return validate_required(value, field, context)

def validate_integer_or_unsure(min_value=None, max_value=None):
	integer_validator = validate_integer(min_value=min_value, max_value=max_value)
	def _validate_integer_or_unsure(value, field, context):
		if type(value) == str and value.strip().strip('"\'').lower() == "unsure":
				return None
		result = integer_validator(value, field, context)
		if result:
			return result + ', or "Unsure"'
	return _validate_integer_or_unsure

form_fields = [
	Field(
		name='admin_type'),
	Field(
		name='citation_agree',
		validators=[val_required_for_submit, val_yn]),
	Field(
		name='citation_agree_comments',
		validators=[]),
	Field(
		name='monitoring_for_trend',
		validators=[val_required_for_submit, val_ynu]),
	Field(
		name='monitoring_for_trend_comments'),
	Field(
		name='analyse_own_trends',
		validators=[val_required_for_submit, val_yn]),
	Field(
		name='analyse_own_trends_comments'),
	Field(
		name='pop_1750',
		validators=[val_required_for_submit, validate_integer_or_unsure(0,100)]),
	Field(
		name='pop_1750_comments'),
	Field(
		name='data_summary_agree',
		validators=[val_required_for_submit, val_yn]),
	Field(
		name='data_summary_agree_comments'),
	Field(
		name='processing_agree',
		validators=[val_required_for_submit, val_ynu]),
	Field(
		name='processing_agree_comments'),
	Field(
		name='statistics_agree',
		validators=[val_required_for_submit, val_ynu]),
	Field(
		name='statistics_agree_comments'),
	Field(
		name='trend_agree',
		validators=[val_required_for_submit, val_ynu]),
	Field(
		name='trend_agree_comments'),
	Field(
		name='start_year',
		type='int',
		validators=[val_required_for_submit, validate_integer_or_unsure(1800,2100)]),
	Field(
		name='start_year_comments'),
	Field(
		name='end_year',
		type='int',
		validators=[val_required_for_submit, validate_integer_or_unsure(1800,2100)]),
	Field(
		name='end_year_comments'),
	Field(
		name='standardisation_of_method_effort',
		validators=[val_required_integrated_only]),
	Field(
		name='objective_of_monitoring',
		validators=[val_required_integrated_only]),
	Field(
		name='consistency_of_monitoring',
		validators=[val_required_integrated_only]),
	Field(
		name='monitoring_frequency_and_timing',
		validators=[val_required_integrated_only]),
	Field(
		name='absences_recorded',
		validators=[val_required_integrated_only]),
	Field(
		name='data_suitability_comments'),


	Field(
		name='cost_data_provided',
		validators=[val_yn]),
	Field(
		name='estimated_cost_dataset',
		validators=[validate_integer_or_unsure()]),
	Field(
		name='cost_data_provided_comments'),
	Field(
		name='custodian_comments'),
	Field(
		name='internal_comments'),

	Field(
		name='monitoring_program_information_contact'),

	Field(
		name='monitoring_program_information_provided'),
	Field(
		name='effort_labour_paid_days_per_year',
		type='int',
		validators=[validate_integer(min_value=0, max_value=365)]),
	Field(
		name='effort_labour_volunteer_days_per_year',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='effort_overheads_paid_days_per_year',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='effort_overheads_volunteer_days_per_year',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='effort_paid_staff_count',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='effort_volunteer_count',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='funding_cost_per_survey_aud',
		type='decimal',
		validators=[validate_decimal(min_value=0,max_dp=2)]),
	Field(
		name='funding_total_investment_aud',
		type='decimal',
		validators=[validate_decimal(min_value=0,max_dp=2)]),
	Field(
		name='funding_source_government_grants',
		validators=[val_yn]),
	Field(
		name='funding_source_research_funds',
		validators=[val_yn]),
	Field(
		name='funding_source_private_donations',
		validators=[val_yn]),
	Field(
		name='funding_source_other'),
	Field(
		name='funding_source_count',
		type='int',
		validators=[validate_integer(min_value=0)]),
	Field(
		name='leadership'),
	Field(
		name='impact_used_for_management',
		validators=[val_yn]),
	Field(
		name='impact_used_for_management_comments'),
	Field(
		name='impact_organisation_responsible'),
	Field(
		name='impact_management_changes'),
	Field(
		name='data_availability'),
	Field(
		name='succession_commitment',
		validators=[val_yn]),
	Field(
		name='succession_commitment_comments'),
	Field(
		name='succession_plan',
		validators=[val_yn]),
	Field(
		name='succession_plan_comments'),
	Field(
		name='design_statistical_power',
		validators=[val_yn]),
	Field(
		name='design_statistical_power_comments'),
	Field(
		name='design_other_factors',
		validators=[val_yn]),
	Field(
		name='design_other_factors_comments'),
	Field(
		name='co_benefits_other_species',
		validators=[val_yn]),
	Field(
		name='co_benefits_other_species_comments'),
	Field(
		name='consent_given',
		type='boolean'),
	Field(
		name='consent_name')
]

def sql_select_clause(identifier, type):
	if type == 'boolean':
		return '(%s = 1)' % identifier
	else:
		return identifier


def get_form_json_raw(form_id):
	answer_select_json_sql = ", ".join(
		"'%s', %s" % (field.name, sql_select_clause('custodian_feedback_answers.' + field.name, field.type)) for field in form_fields)

	rows = db_session.execute(text("""
		SELECT JSON_OBJECT(
			'id', :form_id,
			'dataset_id', dataset_id,
			'time_created', DATE_FORMAT(custodian_feedback.time_created, '%%Y-%%m-%%d %%H:%%i:%%s+00:00'),
			'last_modified', DATE_FORMAT(custodian_feedback.last_modified, '%%Y-%%m-%%d %%H:%%i:%%s+00:00'),
			'last_updated', DATE_FORMAT(custodian_feedback.last_updated, '%%Y-%%m-%%d %%H:%%i:%%s+00:00'),
			'source', JSON_OBJECT(
				'id', source.id,
				'description', source.description,
				'authors', source.authors,
				'details', source.details,
				'provider', source.provider
			),
			'taxon', JSON_OBJECT(
				'id', taxon.id,
				'scientific_name', taxon.scientific_name
			),
			'feedback_type', JSON_OBJECT(
				'code', feedback_type.code,
				'description', feedback_type.description
			),
			'feedback_status', JSON_OBJECT(
				'code', feedback_status.code,
				'description', feedback_status.description
			),
			'answers', JSON_OBJECT(%s),
			'stats', dataset_stats.stats_json
		)
		FROM custodian_feedback
		JOIN source ON custodian_feedback.source_id = source.id
		JOIN taxon ON custodian_feedback.taxon_id = taxon.id
		JOIN feedback_status ON feedback_status.id = custodian_feedback.feedback_status_id
		JOIN feedback_type ON feedback_type.id = custodian_feedback.feedback_type_id
		LEFT JOIN custodian_feedback_answers ON custodian_feedback_answers.custodian_feedback_id = custodian_feedback.id
		LEFT JOIN dataset_stats ON dataset_stats.source_id = source.id AND dataset_stats.taxon_id = taxon.id AND dataset_stats.data_import_id = custodian_feedback.data_import_id
		WHERE custodian_feedback.id = :form_id
	""" % answer_select_json_sql), {
		'form_id': form_id
	})

	rows = list(rows)
	if not rows:
		return None

	[(result,)] = rows
	return result


# ---- Dataset stats logic -----

def update_all_dataset_stats():
	count = 0
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
			count = count + 1
		else:
			break

	return count



def processing_summary(source_id, taxon_id):
	result = db_session.execute(text("""
		SELECT
				search_type.description AS search_type,
				unit.description AS unit,
				unit_type.description AS unit_type,
				data_processing_type.description AS data_processing_type,
				response_variable_type.description AS aggregation_method,
				COUNT(*) = COUNT(DISTINCT start_date_y, site_id) AS annual_data
		FROM
				t1_survey
				JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
				JOIN t1_site ON t1_survey.site_id = t1_site.id
				JOIN search_type ON t1_site.search_type_id = search_type.id
				JOIN unit ON t1_sighting.unit_id = unit.id
				JOIN source ON t1_survey.source_id = source.id
				LEFT JOIN unit_type ON unit.unit_type_id = unit_type.id
				LEFT JOIN data_processing_type ON source.data_processing_type_id = data_processing_type.id
				LEFT JOIN processing_method pm
					ON pm.search_type_id = t1_site.search_type_id
		AND pm.unit_id = t1_sighting.unit_id
		AND pm.taxon_id = t1_sighting.taxon_id
		AND pm.source_id = t1_survey.source_id
		LEFT JOIN response_variable_type ON pm.response_variable_type_id = response_variable_type.id
		WHERE
				t1_survey.source_id = :source_id
				AND t1_sighting.taxon_id = :taxon_id
		GROUP BY
				source.id,
				t1_sighting.taxon_id,
				search_type.id,
				unit.id,
				unit_type.id,
				pm.response_variable_type_id
		"""), {
		'source_id': source_id,
		'taxon_id': taxon_id
	})

	summary_data = [dict(row._mapping) for row in result]

	for row in summary_data:
		if row['annual_data']:
			row['aggregation_method'] = 'Annual data was provided, no aggregation to an annual unit was required.'

	return summary_data

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
	log.info("Updating dataset stats for source_id=%s, taxon_id=%s, data_import_id=%s" % (source_id, taxon_id, data_import_id))

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

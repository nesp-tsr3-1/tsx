from tsx.api.util import db_session
from tsx.api.validation import *
from sqlalchemy import text

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
  "cost_data_provided": [
	{
		"id": "provided",
		"description": "I have provided answers to questions 17 to 32"
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
  ]
}

def val_required_integrated_only(value, field, context):
	if context.submitting and context.feedback_type == 'integrated':
		return validate_required(value, field, context)


form_fields = [
	Field(
		name='citation_agree',
		validators=[val_required_integrated_only, val_yn]),
	Field(
		name='citation_agree_comments',
		validators=[]),
	Field(
		name='monitoring_for_trend',
		validators=[val_required_integrated_only, val_ynu]),
	Field(
		name='monitoring_for_trend_comments'),
	Field(
		name='analyse_own_trends',
		validators=[val_required_integrated_only, val_yn]),
	Field(
		name='analyse_own_trends_comments'),
	Field(
		name='pop_1750',
		type='int',
		validators=[val_required_integrated_only, validate_integer(0,100)]),
	Field(
		name='data_summary_agree',
		validators=[val_required_integrated_only, val_yn]),
	Field(
		name='data_summary_agree_comments'),
	Field(
		name='processing_agree',
		validators=[val_required_integrated_only, val_yn]),
	Field(
		name='processing_agree_comments'),
	Field(
		name='statistics_agree',
		validators=[val_required_integrated_only, val_yn]),
	Field(
		name='statistics_agree_comments'),
	Field(
		name='trend_agree',
		validators=[val_required_integrated_only, val_ynu]),
	Field(
		name='trend_agree_comments'),
	Field(
		name='start_year',
		type='int',
		validators=[val_required_integrated_only, validate_integer(1800,2100)]),
	Field(
		name='end_year',
		type='int',
		validators=[val_required_integrated_only, validate_integer(1800,2100)]),
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
		name='cost_data_provided'),
	Field(
		name='effort_labour_paid_days_per_year',
		type='int'),
	Field(
		name='effort_labour_volunteer_days_per_year',
		type='int'),
	Field(
		name='effort_overheads_paid_days_per_year',
		type='int'),
	Field(
		name='effort_overheads_volunteer_days_per_year',
		type='int'),
	Field(
		name='effort_paid_staff_count',
		type='int'),
	Field(
		name='effort_volunteer_count',
		type='int'),
	Field(
		name='funding_cost_per_survey_aud',
		type='decimal'),
	Field(
		name='funding_total_investment_aud',
		type='decimal'),
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
		type='int'),
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
		name='co_benefits_other_species_comments')
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

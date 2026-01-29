import subprocess
from tests.util import import_test_data, compare_output, get_csv_data
import textwrap

def test_filter_time_series(fresh_database, db_name, output_dir):
    import_test_data(db_name, 'unit',
        csv_data="""\
        id,description
        1,Example Unit
        """)

    import_test_data(db_name, 'source',
        csv_data="""\
        id,source_type_id,provider,description,details,authors,notes,contact_name,contact_institution,contact_position,contact_email,contact_phone,time_created,last_modified,monitoring_program_id,monitoring_program_comments,data_processing_type_id,data_agreement_status_id
        1,1,Example Provider,Example Source,Example Source Details,Example Authors,NULL,Example Contact,Example Institution,NA,test@example.com,NULL,2020-01-01 00:00:00,2020-01-01 00:00:00,NULL,NULL,NULL,4
        """)

    import_test_data(db_name, 'taxon_level',
        csv_data="""\
        id,description
        1,sp
        """)

    import_test_data(db_name, 'taxon',
        csv_data="""\
        id,ultrataxon,taxon_level_id,spno,common_name,scientific_name,family_common_name,family_scientific_name,order,population,epbc_status_id,iucn_status_id,state_status_id,bird_action_plan_status_id,national_priority,taxonomic_group,suppress_spatial_representativeness,eligible_for_tsx
        1,0,1,NULL,Example Common Name,Example SciName,Example Family,Example Family SciName,Example Order,Example Population,3,1,NULL,NULL,0,Example Taxonomic Group,0,1
        """)

    import_test_data(db_name, 'search_type',
        csv_data="""\
        id,description
        1,Example Search Type
        """)

    import_test_data(db_name, 'region',
        csv_data="""\
        id,name,geometry,state,positional_accuracy_in_m
        1,Example Region,000000000106000000010000000103000000010000000500000000000000000000000000000000000000000000000000F03F0000000000000000000000000000F03F000000000000F03F0000000000000000000000000000F03F00000000000000000000000000000000,Example State,0
        """)

    import_test_data(db_name, 'data_source',
        csv_data="""\
        source_id,taxon_id,data_agreement_id,objective_of_monitoring_id,absences_recorded,standardisation_of_method_effort_id,consistency_of_monitoring_id,exclude_from_analysis,start_year,end_year,suppress_aggregated_data,suppress_aggregated_data_until
        1,1,1,1,1,1,1,0,NULL,NULL,0,NULL
        """)

    # Note: 0x00000000010100000000000000000000000000000000000000 = Point(0,0)
    import_test_data(db_name, 'aggregated_by_year',
        csv_data="""\
        start_date_y,site_id,search_type_id,taxon_id,response_variable_type_id,value,data_type,source_id,region_id,unit_id,positional_accuracy_in_m,centroid_coords,survey_count,include_in_analysis
        2001,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
        2002,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
        2003,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
        2004,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
        """)

    import_test_data(db_name, 'custodian_feedback',
        csv_data="""\
        id,source_id,taxon_id,feedback_status_id,feedback_type_id,data_import_id,file_name,time_created,last_modified,last_updated
        1,1,1,1,2,NULL,NULL,2000-01-01 00:00:00,2000-01-01 00:00:00,2000-01-01 00:00:00
        """)

    import_test_data(db_name, 'custodian_feedback_answers',
        csv_data="""\
        custodian_feedback_id,admin_type,citation_agree,citation_agree_comments,monitoring_for_trend,monitoring_for_trend_comments,analyse_own_trends,analyse_own_trends_comments,pop_1750,pop_1750_comments,data_summary_agree,data_summary_agree_comments,processing_agree,processing_agree_comments,statistics_agree,statistics_agree_comments,trend_agree,trend_agree_comments,start_year,start_year_comments,end_year,end_year_comments,standardisation_of_method_effort,objective_of_monitoring,consistency_of_monitoring,monitoring_frequency_and_timing,absences_recorded,data_suitability_comments,additional_comments,cost_data_provided,estimated_cost_dataset,cost_data_provided_comments,custodian_comments,internal_comments,monitoring_program_information_contact,monitoring_program_information_provided,effort_labour_paid_days_per_year,effort_labour_volunteer_days_per_year,effort_overheads_paid_days_per_year,effort_overheads_volunteer_days_per_year,effort_paid_staff_count,effort_volunteer_count,funding_cost_per_survey_aud,funding_total_investment_aud,funding_source_government_grants,funding_source_research_funds,funding_source_private_donations,funding_source_other,funding_source_count,leadership,impact_used_for_management,impact_used_for_management_comments,impact_organisation_responsible,impact_management_changes,data_availability,succession_commitment,succession_commitment_comments,succession_plan,succession_plan_comments,design_statistical_power,design_statistical_power_comments,design_other_factors,design_other_factors_comments,co_benefits_other_species,co_benefits_other_species_comments,consent_name,consent_given,form_version
        1,formal,NULL,NULL,yes,,yes,,,,NULL,NULL,yes,,,,yes,,2000,,,,3,,4,,,,NULL,No,,,,,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1
        """)

    import_test_data(db_name, 'data_source_excluded_years',
        csv_data="""\
        source_id,taxon_id,year
        1,1,2002
        1,1,2003
        """)

    for cmd in [
        ["python", "-m", "tsx.process", "-c", "filter_time_series"]
        ]:
        subprocess.run(cmd).check_returncode()

    expected_csv = textwrap.dedent(
    """\
    start_date_y,site_id,search_type_id,taxon_id,response_variable_type_id,value,data_type,source_id,region_id,unit_id,positional_accuracy_in_m,centroid_coords,survey_count,include_in_analysis
    2001,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,1
    2002,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
    2003,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,0
    2004,0,1,1,1,1,1,1,1,1,0,00000000010100000000000000000000000000000000000000,1,1
    """)
    assert get_csv_data(db_name, 'aggregated_by_year') == expected_csv

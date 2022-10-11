from tsx.db import get_session
import logging
import tsx.config

log = logging.getLogger(__name__)

def process_database():
	session = get_session()

	log.info("Step 1/2 - Building list of filtered time series")

	# Get year range
	min_year = tsx.config.config.getint("processing", "min_year")
	max_year = tsx.config.config.getint("processing", "max_year")
	min_tssy = tsx.config.config.getint("processing", "min_time_series_sample_years")

	session.execute("""CREATE TEMPORARY TABLE tmp_filtered_ts
		( INDEX (time_series_id) )
		SELECT time_series_id
		FROM aggregated_by_year agg
		INNER JOIN taxon ON agg.taxon_id = taxon.id
		LEFT JOIN data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
		WHERE agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
		AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year)
		AND NOT data_source.exclude_from_analysis
		AND COALESCE(agg.search_type_id, 0) != 6
		AND COALESCE(taxon.max_status_id, 0) NOT IN (0,1,7)
		AND region_id IS NOT NULL
		AND COALESCE(data_source.data_agreement_id, -1) NOT IN (0)
		AND COALESCE(data_source.standardisation_of_method_effort_id, -1) NOT IN (0, 1)
		AND COALESCE(data_source.consistency_of_monitoring_id, -1) NOT IN (0, 1)
		AND experimental_design_type_id = 1
		GROUP BY agg.time_series_id
		HAVING MAX(value) > 0
		AND COUNT(DISTINCT start_date_y) >= :min_tssy;
	""", {
		'min_year': min_year,
		'max_year': max_year,
		'min_tssy': min_tssy
	})

	log.info("Step 2/2 - Updating aggregated_by_year table")

	session.execute("""UPDATE aggregated_by_year agg
		LEFT JOIN data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
		SET agg.include_in_analysis =
			agg.time_series_id IN (SELECT time_series_id FROM tmp_filtered_ts)
			AND agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
			AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year)
	""", {
		'min_year': min_year,
		'max_year': max_year
	})

	session.execute("""DROP TABLE tmp_filtered_ts""")

	log.info("Done")


# It could be useful to generate a report listing the reason(s) why time series were excluded
# Following are some queries that could be useful for this:

# CREATE TEMPORARY TABLE excluded
# SELECT DISTINCT taxon_id, unit_id, t1_survey.source_id, search_type_id, 1 AS data_type
# FROM t1_survey
# JOIN t1_site ON t1_site.id = t1_survey.site_id
# JOIN t1_sighting ON t1_survey.id = t1_sighting.survey_id;

# INSERT INTO excluded
# SELECT DISTINCT taxon_id, unit_id, source_id, search_type_id, 2
# FROM t2_survey
# JOIN t2_sighting ON t2_survey.id = t2_sighting.survey_id;

# ^^ (4 min 9.57 sec)

# DELETE FROM excluded
# WHERE (taxon_id, unit_id, source_id, search_type_id, data_type) NOT IN (SELECT taxon_id, unit_id, source_id, search_type_id, data_type FROM aggregated_by_year WHERE include_in_analysis);

# CREATE TEMPORARY TABLE exclusion_reason (
#   taxon_id CHAR(8),
#   unit_id INT,
#   source_id INT,
#   search_type_id INT,
#   data_type INT,
#   reason TEXT
# );

# INSERT INTO exclusion_reason
# SELECT taxon_id, unit_id, source_id, search_type_id, data_type, 'Not present in processing methods file'
# FROM excluded
# WHERE (taxon_id, unit_id, source_id, search_type_id, 1) NOT IN (SELECT taxon_id, unit_id, source_id, search_type_id, data_type FROM processing_method);

# INSERT INTO exclusion_reason
# SELECT taxon_id, unit_id, source_id, search_type_id, data_type, 'Not present in master list'
# FROM excluded
# WHERE (taxon_id, source_id) NOT IN (SELECT taxon_id, source_id FROM data_source);

# INSERT INTO exclusion_reason
# SELECT taxon_id, unit_id, source_id, search_type_id, data_type, 'Excluded by master list (NotInIndex)'
# FROM excluded
# WHERE (taxon_id, source_id) IN (SELECT taxon_id, source_id FROM data_source WHERE exclude_from_analysis);

# INSERT INTO exclusion_reason
# SELECT taxon_id, unit_id, source_id, search_type_id, data_type, 'SearchTypeID = 6 (Incidental)'
# FROM excluded
# WHERE search_type_id = 6;

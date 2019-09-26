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
		AND COALESCE(data_source.data_agreement_id, -1) NOT IN (0, 1)
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

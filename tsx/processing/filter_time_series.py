from tsx.db import get_session
import logging
import tsx.config
from sqlalchemy import text

log = logging.getLogger(__name__)

def process_database():
	session = get_session()

	log.info("Step 1/2 - Building list of filtered time series")

	# Get year range
	min_year = tsx.config.config.getint("processing", "min_year")
	max_year = tsx.config.config.getint("processing", "max_year")
	min_tssy = tsx.config.config.getint("processing", "min_time_series_sample_years")

	session.execute(text("DELETE FROM time_series_inclusion;"))
	session.execute(text("""
		INSERT INTO time_series_inclusion (
			time_series_id,
			sample_years,
			master_list_include,
			search_type,
			taxon_status,
			region,
			data_agreement,
			standardisation_of_method_effort,
			consistency_of_monitoring,
			non_zero)
		SELECT
			time_series_id,
			SUM(
				agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
				AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year)
			) >= :min_tssy, # sample_years
			MAX(COALESCE(NOT data_source.exclude_from_analysis, FALSE)), # master_list_include
			MAX(COALESCE(agg.search_type_id, 0) != 6), # search_type
			MAX(COALESCE(taxon.max_status_id, 0) NOT IN (0,1,7)), # taxon_status
			MAX(region_id IS NOT NULL), # region
			MAX(COALESCE(data_source.data_agreement_id, -1) NOT IN (0)), # data_agreement
			MAX(COALESCE(data_source.standardisation_of_method_effort_id, -1) NOT IN (0, 1)), # standardisation_of_method_effort
			MAX(COALESCE(data_source.consistency_of_monitoring_id, -1) NOT IN (0, 1)), # consistency_of_monitoring
			MAX(IF(agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
					AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year),
				value,
				0)) > 0 # non_zero
		FROM aggregated_by_year agg
		INNER JOIN taxon ON agg.taxon_id = taxon.id
		LEFT JOIN data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
		GROUP BY agg.time_series_id;
	"""), {
		'min_year': min_year,
		'max_year': max_year,
		'min_tssy': min_tssy
	})

	log.info("Step 2/2 - Updating aggregated_by_year table")

	session.execute(text("""UPDATE aggregated_by_year agg
		JOIN time_series_inclusion ON agg.time_series_id = time_series_inclusion.time_series_id
		SET agg.include_in_analysis = time_series_inclusion.include_in_analysis"""))

	session.commit()

	log.info("Done")

from tsx.db import get_session
import logging
import tsx.config
from sqlalchemy import text

log = logging.getLogger(__name__)

def process_database():
    session = get_session()

    log.info("Step 1/3 - Update data source information")

    sql_stmts = [
        """
        CREATE TEMPORARY TABLE cf_data_source
        WITH t AS (
            SELECT
                custodian_feedback_id,
                feedback_type_id,
                source_id,
                taxon_id,
                dense_rank() over (partition by source_id, taxon_id order by feedback_type_id = 2, last_updated) AS r,
                NULLIF(objective_of_monitoring, '') AS objective_of_monitoring_id,
                NULLIF(standardisation_of_method_effort, '') AS standardisation_of_method_effort_id,
                NULLIF(consistency_of_monitoring, '') AS consistency_of_monitoring_id,
                CASE coalesce(absences_recorded, '')
                    WHEN 'yes' THEN 1
                    WHEN 'no' THEN 0
                    WHEN 'partially' THEN 0
                    ELSE NULL
                END AS absences_recorded
            FROM custodian_feedback
            JOIN custodian_feedback_answers ON custodian_feedback_id = custodian_feedback.id
            WHERE (
                (feedback_type_id = 2) OR
                (feedback_type_id = 1 AND feedback_status_id IN (3,4))
            )
        )
        SELECT * FROM t WHERE r = 1
        """,
        """
        DROP TABLE IF EXISTS data_source_merged;
        """,
        """
        CREATE TABLE data_source_merged (
            PRIMARY KEY(source_id, taxon_id)
        ) SELECT
            a.source_id,
            a.taxon_id,
            b.objective_of_monitoring_id,
            b.absences_recorded,
            b.standardisation_of_method_effort_id,
            b.consistency_of_monitoring_id,
            a.exclude_from_analysis,
            a.start_year,
            a.end_year,
            a.suppress_aggregated_data
        FROM data_source a
        JOIN cf_data_source b ON a.source_id = b.source_id AND a.taxon_id = b.taxon_id;
        """
    ]

    for sql in sql_stmts:
        session.execute(text(sql))


    # Now we have to change everything to use data_source_merged instead of data_source

    log.info("Step 2/3 - Building list of filtered time series")

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
            MAX(source.data_agreement_status_id NOT IN (1, 2, 3)), # data_agreement
            MAX(COALESCE(data_source.standardisation_of_method_effort_id, -1) NOT IN (0, 1)), # standardisation_of_method_effort
            MAX(COALESCE(data_source.consistency_of_monitoring_id, -1) NOT IN (0, 1)), # consistency_of_monitoring
            MAX(IF(agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
                    AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year),
                value,
                0)) > 0 # non_zero
        FROM aggregated_by_year agg
        INNER JOIN taxon ON agg.taxon_id = taxon.id
        INNER JOIN source ON agg.source_id = source.id
        LEFT JOIN data_source_merged AS data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
        GROUP BY agg.time_series_id;
    """), {
        'min_year': min_year,
        'max_year': max_year,
        'min_tssy': min_tssy
    })

    log.info("Step 3/3 - Updating aggregated_by_year table")

    session.execute(text("""UPDATE aggregated_by_year agg
        JOIN time_series_inclusion ON agg.time_series_id = time_series_inclusion.time_series_id
        LEFT JOIN data_source_merged AS data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
        SET agg.include_in_analysis = (
            time_series_inclusion.include_in_analysis
            AND agg.start_date_y <= COALESCE(data_source.end_year, :max_year)
            AND agg.start_date_y >= COALESCE(data_source.start_year, :min_year)
        )"""), {
        'min_year': min_year,
        'max_year': max_year
    })

    session.commit()

    log.info("Done")

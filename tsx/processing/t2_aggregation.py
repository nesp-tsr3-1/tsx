import logging
import time
from tqdm import tqdm
from tsx.db import get_session
from tsx.util import run_parallel, sql_list_placeholder, sql_list_argument
from sqlalchemy import text
from random import shuffle

log = logging.getLogger(__name__)

def process_database(species = None, commit = False, database_config = None):
    session = get_session(database_config)
    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute(text("SELECT DISTINCT taxon_id FROM processing_method")).fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            text("SELECT DISTINCT taxon_id FROM t1_sighting, taxon WHERE taxon.id = taxon_id AND spno IN (%s)" % sql_list_placeholder('species', species)),
            sql_list_argument('species', species)).fetchall()]

    shuffle(taxa)

    sql = """
        SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

        DROP TABLE IF EXISTS tmp_site_centroid;

        CREATE TABLE tmp_site_centroid
        AS SELECT
            site_id,
            ST_Centroid(ST_Collect(coords)) AS centroid
        FROM t2_survey
        WHERE site_id IS NOT NULL
        GROUP BY site_id;

        ALTER TABLE tmp_site_centroid ADD COLUMN region_id INT;

        ALTER TABLE tmp_site_centroid CHANGE COLUMN centroid centroid POINT SRID 0 NOT NULL;

        UPDATE /*+ JOIN_ORDER(tmp_site_centroid, region_subdiv) */
        tmp_site_centroid, region_subdiv
        SET region_id = region_subdiv.id
        WHERE ST_Intersects(centroid, geometry);

        ALTER TABLE tmp_site_centroid ADD SPATIAL INDEX centroid (centroid);

        ALTER TABLE tmp_site_centroid ADD INDEX site_id (site_id)
    """

    log.info("Pre-processing")
    for stmt in tqdm(sql.split(";")):
        run_sql(session, stmt)

    # Process taxa in parallel
    tasks = [(taxon_id, commit, database_config) for taxon_id in taxa]

    session.close() # Important to close session before spawning multiple processes

    log.info("Performing aggregation")

    for result, error in tqdm(run_parallel(process_task, tasks), total=len(tasks)):
        if error:
            print(error)
            print("Shutting down due to error")
            exit()

    # Clean up
    session = get_session(database_config)
    run_sql(session, "DROP TABLE tmp_site_centroid")

def run_sql(session, sql, *args, **kwargs):
    short_sql = sql.replace("\n", " ")[:100]
    # print(short_sql)
    t0 = time.time()
    session.execute(text(sql), *args, **kwargs)
    t1 = time.time()
    # print("%s took %s sec" % (short_sql, t1 - t0))

def process_task(taxon_id, commit=False, database_config=None):
    session = get_session(database_config)

    sql = """
        -- Go faster
        SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

        -- Fix for annoying character collation issue
        SET @taxon_id = (SELECT id FROM taxon WHERE id = :taxon_id);

        SET @species_id = (
            SELECT id FROM taxon
            WHERE spno = (SELECT spno FROM taxon WHERE taxon.id = @taxon_id)
            AND taxon_level_id = (SELECT id FROM taxon_level WHERE description = 'sp'));

        -- Find sites where this taxon is present
        CREATE TEMPORARY TABLE tmp_site_taxon AS
        SELECT DISTINCT
            site_id,
            taxon_id
        FROM taxon_presence_alpha_hull_subdiv alpha, t2_survey
        WHERE ST_Contains(alpha.geometry, t2_survey.coords)
        AND alpha.range_id = 1
        AND alpha.taxon_id = @taxon_id;

        -- Find all sightings and pseudo-absences
        CREATE TEMPORARY TABLE tmp_sighting AS
            WITH species_taxon AS (
                SELECT t1.id
                FROM taxon t1, taxon t2
                WHERE t1.spno = t2.spno
                AND t2.id = @taxon_id
                AND NOT t1.ultrataxon
            )
            -- Pseudo-absences and presences based on spno or taxon_id match
            SELECT t2_survey.id AS survey_id, t2_sighting.id AS sighting_id
            FROM t2_survey
            JOIN tmp_site_taxon ON tmp_site_taxon.site_id = t2_survey.site_id
            LEFT JOIN t2_sighting ON t2_sighting.survey_id = t2_survey.id AND t2_sighting.taxon_id IN (@taxon_id, @species_id)
            ;

        -- Aggregate to monthly time series
        CREATE TEMPORARY TABLE tmp_survey_agg AS
            WITH t AS (
                SELECT
                    t2_survey.start_date_y AS year,
                    t2_survey.start_date_m AS month,
                    t2_survey.site_id,
                    t2_survey.search_type_id,
                    t2_survey.source_id,
                    @taxon_id AS taxon_id,
                    MAX(t2_survey.positional_accuracy_in_m) AS positional_accuracy_in_m,
                    AVG(ST_X(t2_survey.coords)) AS centroid_x,
                    AVG(ST_Y(t2_survey.coords)) AS centroid_y,
                    COUNT(DISTINCT t2_survey.id) AS num_surveys,
                    # COUNT(*) AS num_surveys, -- This version is compatible with old workflow
                    COUNT(t2_sighting.id) AS num_sightings,
                    COALESCE(SUM(t2_sighting.unit_id = 1), 0) AS num_po_sightings,
                    COALESCE(SUM(t2_sighting.unit_id != 1), 0) AS num_count_sightings,
                    COALESCE(SUM(t2_sighting.count * (t2_sighting.unit_id != 1)), 0) AS sum_of_counts,
                    COALESCE(MAX(t2_sighting.count * (t2_sighting.unit_id != 1)), 0) AS max_count
                FROM tmp_sighting
                JOIN t2_survey ON t2_survey.id = tmp_sighting.survey_id
                LEFT JOIN t2_sighting ON tmp_sighting.sighting_id = t2_sighting.id

                -- Extra conditions as per old workflow

                WHERE t2_survey.search_type_id != 6
                AND COALESCE(t2_survey.duration_in_minutes <= 6 * 60, TRUE)
                AND COALESCE((t2_survey.start_date_y, t2_survey.start_date_m, t2_survey.start_date_d) = (t2_survey.finish_date_y, t2_survey.finish_date_m, t2_survey.finish_date_d), TRUE)

                GROUP BY
                    year, month, site_id, search_type_id, source_id
            )
            SELECT
                *,
                ROUND(1.0 * num_sightings / num_surveys, 2) AS rr,
                -- COALESCE(1.0 * sum_of_counts / NULLIF(num_count_sightings, 0), 0) AS mean_of_count, -- not including absences
                1.0 * sum_of_counts / NULLIF(num_surveys - num_po_sightings, 0) AS mean_abundance -- including absences as 0s [Will be null if there are no count sightings]
            FROM t;


        -- Insert results into permanent table
        INSERT INTO aggregated_by_month (
            start_date_y,
            start_date_m,
            site_id,
            search_type_id,
            taxon_id,
            response_variable_type_id,
            value,
            data_type,
            source_id,
            region_id,
            unit_id,
            positional_accuracy_in_m,
            centroid_coords,
            survey_count
        )
        SELECT
            year,
            month,
            site_id,
            search_type_id,
            taxon_id,
            response_variable_type.id,
            CASE response_variable_type.id
                WHEN 1 THEN mean_abundance -- avg count
                WHEN 2 THEN max_count -- max count
                WHEN 3 THEN rr -- reporting rate
                ELSE NULL
            END AS value,
            2,
            source_id,
            (SELECT region_id FROM tmp_site_centroid WHERE tmp_site_centroid.site_id = tmp_survey_agg.site_id),
            CASE response_variable_type.id
                WHEN 1 THEN 2 -- avg count => abundance
                WHEN 2 THEN 2 -- max count => abundance
                WHEN 3 THEN 1 -- reporting rate => occupancy
                ELSE NULL
            END,
            positional_accuracy_in_m,
            Point(centroid_x, centroid_y),
            num_surveys
        FROM tmp_survey_agg, response_variable_type
        -- Comment out following to ignore processing_method table
        WHERE (taxon_id, source_id, 2, response_variable_type.id) IN
        (SELECT taxon_id, source_id, data_type, response_variable_type_id FROM processing_method)

        HAVING value IS NOT NULL;

        -- Yearly aggregation
        INSERT INTO aggregated_by_year (
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                taxon_id,
                response_variable_type_id,
                value,
                data_type,
                region_id,
                unit_id,
                positional_accuracy_in_m,
                centroid_coords,
                survey_count)
            SELECT
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                taxon_id,
                response_variable_type_id,
                AVG(value),
                data_type,
                region_id,
                unit_id,
                MAX(positional_accuracy_in_m) AS positional_accuracy_in_m,
                Point(AVG(ST_X(centroid_coords)), AVG(ST_Y(centroid_coords))),
                SUM(survey_count)
            FROM aggregated_by_month
            WHERE taxon_id = :taxon_id
            AND data_type = 2
            GROUP BY
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                taxon_id,
                response_variable_type_id,
                data_type,
                region_id,
                unit_id;

        DROP TABLE tmp_sighting;
        DROP TABLE tmp_survey_agg;
        DROP TABLE tmp_site_taxon
    """

    for stmt in sql.split(";"):
        run_sql(session, stmt, { 'taxon_id': taxon_id })

    session.commit()
    session.close()

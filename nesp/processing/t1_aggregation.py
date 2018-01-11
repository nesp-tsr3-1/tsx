import logging
import time
import functools
from tqdm import tqdm
from nesp.db import get_session
from nesp.util import run_parallel


log = logging.getLogger(__name__)

def process_database(species = None, commit = False):
    session = get_session()
    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM t1_sighting").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            "SELECT DISTINCT taxon_id FROM t1_sighting, taxon WHERE taxon.id = taxon_id AND spno IN :species", {
                'species': species
            }).fetchall()]

    create_region_lookup_table(session)

    # Process in parallel
    tasks = [(taxon_id, commit) for taxon_id in taxa]

    log.info("Step 1/2: Monthly aggregation")

    for result, error in tqdm(run_parallel(aggregate_monthly, tasks), total=len(tasks)):
        if error:
            print error

    log.info("Step 1/2: Yearly aggregation")

    for result, error in tqdm(run_parallel(aggregate_yearly, tasks), total=len(tasks)):
        if error:
            print error

    cleanup_region_lookup_table(session)


def aggregate_monthly(taxon_id, commit = False):
    session = get_session()
    try:
        sql = """SELECT source_id, unit_id, search_type_id, experimental_design_type_id, response_variable_type_id
            FROM processing_method
            WHERE data_type = 1
            AND taxon_id = :taxon_id"""
        rows = session.execute(sql, {'taxon_id': taxon_id}).fetchall()

        for source_id, unit_id, search_type_id, experimental_design_type_id, response_variable_type_id in rows:

            if experimental_design_type_id != 1:
                raise ValueError("Unexpected experimental_design_type_id: %s (only '1' is supported)" % experimental_design_type_id)

            # Tweak SQL based on response variable type

            where_conditions = []

            if response_variable_type_id == 1:
                aggregate_expression = 'AVG(count)'
                where_conditions.append("unit_id > 1")

            elif response_variable_type_id == 2:
                aggregate_expression = 'MAX(count)'
                where_conditions.append("unit_id > 1")

            elif response_variable_type_id == 3:
                aggregate_expression = 'AVG(count > 0)'
                where_conditions.append("unit_id = 1")


            # ingest into the table
            sql = """INSERT INTO aggregated_by_month (
                start_date_y,
                start_date_m,
                source_id,
                site_id,
                search_type_id,
                taxon_id,
                experimental_design_type_id,
                response_variable_type_id,
                value,
                region_id,
                positional_accuracy_in_m,
                unit_id,
                data_type,
                centroid_coords,
                survey_count)
            SELECT
                start_date_y,
                start_date_m,
                survey.source_id,
                site_id,
                search_type_id,
                taxon_id,
                1,
                :response_variable_type_id,
                {aggregate_expression},
                MIN((SELECT MIN(region_id) FROM tmp_region_lookup t WHERE t.site_id = survey.site_id)),
                MAX(positional_accuracy_in_m),
                unit_id,
                1,
                Point(AVG(ST_X(survey.coords)), AVG(ST_Y(survey.coords))),
                COUNT(*)
            FROM t1_survey survey
            INNER JOIN
                t1_site site ON site.id = survey.site_id
            INNER JOIN
                t1_sighting sighting ON sighting.survey_id = survey.id
            WHERE
                taxon_id = :taxon_id
                AND survey.source_id = :source_id
                AND unit_id = :unit_id
                AND search_type_id = :search_type_id
                {where_conditions}
            GROUP BY
                start_date_y, start_date_m, site_id
            """.format(
                    aggregate_expression = aggregate_expression,
                    where_conditions = " ".join("AND %s" % cond for cond in where_conditions)
                )

            session.execute(sql, {
                'taxon_id': taxon_id,
                'response_variable_type_id': response_variable_type_id,
                'source_id': source_id,
                'unit_id': unit_id,
                'search_type_id': search_type_id
            })

        if commit:
            session.commit()

    except:
        log.exception("Exception aggregating taxon: %s" % taxon_id)
        raise
    finally:
        session.close()



def aggregate_yearly(taxon_id, commit = False):
    session = get_session()
    try:
        sql = """
            INSERT INTO aggregated_by_year (
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                grid_cell_id,
                taxon_id,
                experimental_design_type_id,
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
                grid_cell_id,
                taxon_id,
                experimental_design_type_id,
                response_variable_type_id,
                AVG(value),
                data_type,
                region_id,
                unit_id,
                positional_accuracy_in_m,
                Point(AVG(ST_X(centroid_coords)), AVG(ST_Y(centroid_coords))),
                SUM(survey_count)
            FROM aggregated_by_month
            WHERE taxon_id = :taxon_id
            AND data_type = 1
            GROUP BY
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                grid_cell_id,
                taxon_id,
                experimental_design_type_id,
                response_variable_type_id,
                data_type,
                region_id,
                unit_id,
                positional_accuracy_in_m
        """

        session.execute(sql, { 'taxon_id': taxon_id })

        if commit:
            session.commit()
    except:
        log.exception("Exception aggregating taxon: %s" % taxon_id)
        raise
    finally:
        session.close()



def cleanup_region_lookup_table(session):
    session.execute("""DROP TABLE IF EXISTS tmp_region_lookup""")

def create_region_lookup_table(session):
    log.info("Pre-calculating region for each site")

    cleanup_region_lookup_table(session)
    session.execute("""CREATE TABLE tmp_region_lookup
        ( INDEX (site_id) )
        SELECT DISTINCT
            site_id,
            region_subdiv.id AS region_id
        FROM
            t1_survey
        STRAIGHT_JOIN region_subdiv USE INDEX (geometry) ON ST_Intersects(coords, geometry)
        """)

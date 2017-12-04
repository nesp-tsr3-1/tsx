from nesp.db import get_session
from tqdm import tqdm
import logging
from nesp.util import run_parallel
import time
import functools

log = logging.getLogger(__name__)

def process_database(species = None, commit = False):
    session = get_session()

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM t2_processed_sighting").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            "SELECT DISTINCT taxon_id FROM t2_processed_sighting, taxon WHERE taxon.id = taxon_id AND spno IN :species", {
                'species': species
            }).fetchall()]

    log.info("Step 1/2: Monthly aggregation")

    fn = functools.partial(aggregate_by_month, commit = commit)

    for result, error in tqdm(run_parallel(fn, taxa), total = len(taxa)):
        pass

    log.info("Step 2/2: Yearly aggregation")

    fn = functools.partial(aggregate_by_year, commit = commit)

    for result, error in tqdm(run_parallel(fn, taxa), total = len(taxa)):
        pass


def aggregate_by_month(taxon_id, commit = False):
    session = get_session()
    try:
        # TODO: load this from taxon spreadhseet
        # (Just generating random combinations now for test purposes)
        experimental_design_type_id = (hash(taxon_id) % 3) + 1
        response_variable_type_id = (hash('_' + taxon_id) % 3) + 1

        where_conditions = []

        # Tweak SQL based on response variable type

        if response_variable_type_id == 1:
            aggregate_expression = 'AVG(count)'
            where_conditions.append("unit_id > 1")

        elif response_variable_type_id == 2:
            aggregate_expression = 'MAX(count)'
            where_conditions.append("unit_id > 1")

        elif response_variable_type_id == 3:
            aggregate_expression = 'AVG(count > 0)'

        # Tweak SQL based on experimental design type

        if experimental_design_type_id == 1:
            fields = 'site_id, search_type_id'
            where_conditions.append("site_id IS NOT NULL")

        elif experimental_design_type_id == 2:
            fields = 'grid_cell_id, search_type_id'
            where_conditions.append("grid_cell_id IS NOT NULL")

        elif experimental_design_type_id == 3:
            fields = 'grid_cell_id'
            where_conditions.append("grid_cell_id IS NOT NULL")

        # Generate SQL for monthly aggregation

        sql = """INSERT INTO aggregated_by_month (
            start_date_y,
            start_date_m,
            source_id,
            {fields},
            taxon_id,
            experimental_design_type_id,
            response_variable_type_id,
            value,
            data_type)
        SELECT
            start_date_y,
            start_date_m,
            source_id,
            {fields},
            taxon_id,
            :experimental_design_type_id,
            :response_variable_type_id,
            {aggregate_expression},
            2
        FROM
            t2_processed_survey survey
            INNER JOIN t2_processed_sighting sighting ON survey_id = survey.id
        WHERE taxon_id = :taxon_id
        AND raw_survey_id IN (
            SELECT id
            FROM t2_survey
            WHERE COALESCE(positional_accuracy_in_m < 500, TRUE) # TODO: base this on taxon spreadsheet
            AND COALESCE(duration_in_minutes <= 6 * 60, TRUE)
            AND COALESCE((t2_survey.start_date_y, t2_survey.start_date_m, start_date_d) = (finish_date_y, finish_date_m, finish_date_d), TRUE)
        )
        {where_conditions}
        GROUP BY
            start_date_y,
            start_date_m,
            source_id,
            {fields}
        """.format(
                aggregate_expression = aggregate_expression,
                where_conditions = " ".join("AND %s" % cond for cond in where_conditions),
                fields = fields
            )

        session.execute(sql, {
            'experimental_design_type_id': experimental_design_type_id,
            'response_variable_type_id': response_variable_type_id,
            'taxon_id': taxon_id
        })

        if commit:
            session.commit()

    except:
        log.exception("Exception processing taxon: %s" % taxon_id)
        raise
    finally:
        session.close()



def aggregate_by_year(taxon_id, commit = False):
    session = get_session()
    try:
        # Now perform yearly aggregation
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
                data_type)
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
                data_type
            FROM aggregated_by_month
            WHERE taxon_id = :taxon_id
            GROUP BY
                start_date_y,
                source_id,
                search_type_id,
                site_id,
                grid_cell_id,
                taxon_id,
                experimental_design_type_id,
                response_variable_type_id,
                value,
                data_type
        """

        session.execute(sql, { 'taxon_id': taxon_id })

        if commit:
            session.commit()
    except:
        log.exception("Exception processing taxon: %s" % taxon_id)
        raise
    finally:
        session.close()

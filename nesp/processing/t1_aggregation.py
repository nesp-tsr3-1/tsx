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
     # Unwrap tuple
    taxa = [taxon_id for (taxon_id) in taxa]

    # Process in parallel
    tasks = [(taxon_id, commit) for taxon_id in taxa]

    for result, error in tqdm(run_parallel(aggregate_monthly, tasks), total=len(tasks)):
        if error:
            print error

    for result, error in tqdm(run_parallel(aggregate_yearly, tasks), total=len(tasks)):
        if error:
            print error


def aggregate_monthly(taxon_id, commit = False):
    log.info("[t1_aggregation::aggregate_monthly] Monthly aggregation")
    session = get_session()
    try:
        # ingest into the table
        sql = """INSERT INTO t1_monthly_aggregation (
            start_date_y,
            start_date_m,
            site_id,
            search_type_id,
            taxon_id,
            count,
            source_id,
            coords)
        SELECT
            start_date_y,
            start_date_m,
            site_id,
            search_type_id,
            taxon_id,
			AVG(count) as count, 
            survey.source_id,
            coords
        FROM t1_survey survey
		INNER JOIN 
			t1_site site ON site.id = survey.site_id
		INNER JOIN 
			t1_sighting sighting ON sighting.survey_id = survey.id
		WHERE 
			taxon_id = :taxon_id
		GROUP BY
		    start_date_y, start_date_m, site_id, search_type_id, taxon_id, source_id, coords
        """

        session.execute(sql, {
            'taxon_id': taxon_id
        })

        if commit:
            session.commit()

    except:
        log.exception("Exception aggregating taxon: %s" % taxon_id)
        raise
    finally:
        session.close()



def aggregate_yearly(taxon_id, commit = False):
    log.info("[t1_aggregation::aggregate_yearly] Yearly aggregation")
    session = get_session()
    try:
        sql = """
            INSERT INTO t1_yearly_aggregation (
                start_date_y,
	            site_id,
	            search_type_id,
	            taxon_id,
	            count,
	            source_id,
	            subibra_id,
	            subibra_name)
            SELECT
                start_date_y,
	            site_id,
	            search_type_id,
	            taxon_id,
		    AVG(count) as count, 
	            source_id,
	            subibra.subibra_id as subibra_id,
	            subibra.name as subibra_name
            FROM t1_monthly_aggregation
            INNER JOIN 
            	subibra ON ST_Within(t1_monthly_aggregation.coords, subibra.SHAPE)
            WHERE
		taxon_id = :taxon_id
	    GROUP BY
                start_date_y, site_id, search_type_id, taxon_id, source_id, subibra_id, subibra_name
        """

        session.execute(sql, { 'taxon_id': taxon_id })

        if commit:
            session.commit()
    except:
        log.exception("Exception aggregating taxon: %s" % taxon_id)
        raise
    finally:
        session.close()

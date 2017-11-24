from nesp.db import get_session
from tqdm import tqdm
import logging
from nesp.util import run_parallel
import time
log = logging.getLogger(__name__)

def process_database(commit = False):
    session = get_session()

    def run_sql(msg, sql):
        log.info(msg)
        t1 = time.time()
        r = session.execute(sql)
        t2 = time.time()
        log.info("  Rows affected: %s (%0.2fs)" % (r.rowcount, t2 - t1))

    taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM taxon_presence_alpha_hull_subdiv").fetchall()]

    session.execute("""DROP TABLE IF EXISTS t2_aggregate""")

    session.execute("""CREATE TABLE t2_aggregate (
            start_date_y SMALLINT,
            search_type_id INT,
            site_id INT,
            taxon_id CHAR(6),
            value DOUBLE
        )""")

    def process_taxon(taxon_id):
        session = get_session()
        try:
            session.execute("""
                INSERT INTO t2_aggregate
                SELECT
                    start_date_y,
                    search_type_id,
                    site_id,
                    taxon_id,
                    AVG(monthly_average) AS average
                FROM
                    (SELECT
                        start_date_y,
                        start_date_m,
                        search_type_id,
                        site_id,
                        taxon_id,
                        AVG(count) AS monthly_average
                    FROM
                        t2_processed_survey survey,
                        t2_processed_sighting sighting
                    WHERE sighting.survey_id = survey.id
                    AND taxon_id = :taxon_id
                    GROUP BY
                        start_date_y,
                        start_date_m,
                        search_type_id,
                        site_id) t
                GROUP BY
                    start_date_y,
                    search_type_id,
                    site_id
            """, {
                'taxon_id': taxon_id
            })
        except:
            log.exception("Exception processing taxon: %s" % taxon_id)
            raise
        finally:
            session.close()

    for result, error in tqdm(run_parallel(process_taxon, taxa), total = len(taxa)):
        pass
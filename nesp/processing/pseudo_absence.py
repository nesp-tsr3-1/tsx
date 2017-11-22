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

	run_sql("Delete previous sightings",
		"""DELETE t2_processed_sighting
			FROM t2_processed_sighting, t2_processed_survey
			WHERE t2_processed_sighting.survey_id = t2_processed_survey.id
			AND t2_processed_survey.site_id IS NOT NULL""")

	run_sql("Delete previous surveys",
		"""DELETE FROM t2_processed_survey
			WHERE t2_processed_survey.site_id IS NOT NULL""")

	run_sql("Delete previous t2_survey_site entries",
		"""DELETE FROM t2_survey_site""")

	run_sql("Populate t2_survey_site",
		"""INSERT INTO t2_survey_site (survey_id, site_id)
			SELECT t2_survey.id, t2_site.id
			FROM t2_survey, t2_site
			WHERE site_id = t2_site.id""")
	# Query OK, 14073 rows affected (0.68 sec)
	# Records: 14073  Duplicates: 0  Warnings: 0

	run_sql("Populate t2_survey_site (spatial)",
		"""INSERT INTO t2_survey_site
			SELECT t2_survey.id, t2_site.id
			FROM t2_site STRAIGHT_JOIN t2_survey USE INDEX (coords)
			WHERE site_id IS NULL
			AND t2_survey.search_type_id = t2_site.search_type_id
			AND ST_Intersects(geometry, coords)""")
	# Query OK, 278678 rows affected (15.77 sec)
	# Records: 278678  Duplicates: 0  Warnings: 0

	run_sql("Populate standardised site surveys",
		"""INSERT INTO t2_processed_survey (raw_survey_id, site_id, search_type_id, start_date_y, start_date_m, experimental_design_type_id)
			SELECT t2_survey.id, t2_survey_site.site_id, search_type_id, start_date_y, start_date_m, 1
			FROM t2_survey, t2_survey_site
			WHERE t2_survey.id = t2_survey_site.survey_id""")
	# Query OK, 292751 rows affected (5.00 sec)
	# Records: 292751  Duplicates: 0  Warnings: 0

	run_sql("Populate presences / non-pseudo-absences",
		"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
			SELECT t2_processed_survey.id, t2_ultrataxon_sighting.taxon_id, count, unit_id, 0
			FROM t2_ultrataxon_sighting, t2_sighting, t2_processed_survey
			WHERE t2_ultrataxon_sighting.sighting_id = t2_sighting.id
			AND t2_sighting.survey_id = t2_processed_survey.raw_survey_id
			AND t2_processed_survey.experimental_design_type_id = 1""")
	# Query OK, 5775718 rows affected (2 min 35.55 sec)
	# Records: 5775718  Duplicates: 0  Warnings: 0

	# session.commit()
	# return

	log.info("Identify taxa for each site based on alpha hulls")

	taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM taxon_presence_alpha_hull_subdiv").fetchall()]
	session.execute("""CREATE TEMPORARY TABLE tmp_taxon_site (
		site_id INT NOT NULL,
		taxon_id CHAR(6) NOT NULL,
		INDEX (site_id),
		INDEX (taxon_id)
	)""")

	# The next step was originally a very slow query, directly populating the tmp_taxon_site table.
	# Instead, I've broken the query down to process one taxon at a time
	# Furthermore, we process taxa in parallel threads to fully utilise the CPU, and then the results of the query are
	# inserted in bulk on the main thread.
	# Time taken: 17 min 4 s

	def get_taxon_sites(taxon_id):
		session = get_session()
		try:
			return session.execute("""SELECT DISTINCT t2_survey_site.site_id, taxon_id
				FROM taxon_presence_alpha_hull_subdiv alpha STRAIGHT_JOIN t2_survey USE INDEX (coords), t2_survey_site
				WHERE ST_Contains(alpha.geometry, t2_survey.coords)
				AND t2_survey_site.survey_id = t2_survey.id
				AND taxon_id = :taxon_id
				AND alpha.range_id = 1""", {
					'taxon_id': taxon_id
				}).fetchall()
		except:
			log.exception("Exception getting sites for taxon")
			raise
		finally:
			session.close()

	for result, error in tqdm(run_parallel(get_taxon_sites, taxa), total = len(taxa)):
		# Perform bulk insert on main thread
		if len(result) > 0:
			insert_data = [{ 'site_id': site_id, 'taxon_id': taxon_id } for site_id, taxon_id in result]
			session.execute("""INSERT INTO tmp_taxon_site (site_id, taxon_id) VALUES (:site_id, :taxon_id)""", insert_data)

	# This query is a bit tricky. We do a left join to find taxons that are not present for a survey, and match on
	# t2_processed_sighting.id = NULL to generate the pseudo-absences
	run_sql("Populate pseudo absences",
		"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
			SELECT t2_processed_survey.id, tmp_taxon_site.taxon_id, 0, 2, 1
			FROM t2_survey
			INNER JOIN t2_survey_site ON t2_survey.id = t2_survey_site.survey_id
			INNER JOIN t2_processed_survey ON t2_survey.id = t2_processed_survey.raw_survey_id AND t2_processed_survey.experimental_design_type_id = 1
			INNER JOIN tmp_taxon_site ON t2_survey_site.site_id = tmp_taxon_site.site_id
			LEFT JOIN t2_processed_sighting ON t2_processed_sighting.survey_id = t2_processed_survey.id AND t2_processed_sighting.taxon_id = tmp_taxon_site.taxon_id
			WHERE t2_processed_sighting.id IS NULL""")
	# Query OK, 49926906 rows affected (15 min 21.20 sec)
	# Records: 49926906  Duplicates: 0  Warnings: 0

	if commit:
		log.info("Committing changes")
		session.commit()
	else:
		log.info("Rolling back changes (dry-run only)")
		session.rollback()


# """CREATE TEMPORARY TABLE tmp_taxon_grid
# SELECT DISTINCT grid_cell.id AS grid_cell_id, alpha.taxon_id
# FROM grid_cell, taxon_presence_alpha_hull_subdiv alpha USE INDEX (geometry)
# WHERE alpha.range_id = 1
# AND ST_Intersects(grid_cell.geometry, alpha.geometry)
# """
# # Query OK, 1644638 rows affected (3 min 22.52 sec)
# # Records: 1644638  Duplicates: 0  Warnings: 0

# """CREATE TEMPORARY TABLE tmp_survey_grid
# SELECT t2_survey.id AS survey_id, grid_cell.id AS grid_cell_id
# FROM t2_survey, grid_cell
# WHERE ST_Contains(grid_cell.geometry, t2_survey.coords)
# """
# # Query OK, 1021487 rows affected (1 min 40.73 sec)
# # Records: 1021487  Duplicates: 0  Warnings: 0



from tsx.db import get_session
from tqdm import tqdm
import logging
from tsx.util import run_parallel
import time
import tempfile
from sqlalchemy import text

log = logging.getLogger(__name__)

# I originally wanted to make this able to process each taxon separately, however this is not trivial to implement
# It's much easier to generate the whole dataset for all taxa in one go.
def process_database(commit = False):

	if not commit:
		log.info("Dry-run not supported. Pass -c option.")
		return

	session = get_session()

	# This speeds up the t2_survey_site spatial query by a factor of about 6
	session.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

	if not (is_empty(session, "t2_processed_survey") and is_empty(session, "t2_survey_site")):
		log.error("Existing outputs found - please drop and recreate these tables first: t2_processed_sighting, t2_processed_survey, t2_survey_site")
		log.info("""Run:
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE t2_processed_sighting;
TRUNCATE t2_processed_survey;
TRUNCATE t2_survey_site;
SET FOREIGN_KEY_CHECKS = 1;
			""")
		return

	process_sites(session)
	process_grid(session)

	session.commit();

def process_grid(session):
	taxa = [taxon_id for (taxon_id,) in session.execute(text("""SELECT DISTINCT taxon_id
		FROM processing_method
		WHERE data_type = 2
		AND experimental_design_type_id IN (2, 3)""")).fetchall()
	]

	if len(taxa) == 0:
		log.info("No taxa with grid experimental design types - skipping grid processing")
		return

	# Notes - times are with a warm buffer pool, first run was not so fast

	run_sql(session, "Intersecting alpha hulls with grid",
		"""CREATE TEMPORARY TABLE tmp_taxon_grid
			(INDEX(taxon_id, grid_cell_id))
			SELECT DISTINCT grid_cell.id AS grid_cell_id, alpha.taxon_id
			FROM grid_cell, taxon_presence_alpha_hull_subdiv alpha
			WHERE alpha.range_id = 1
			AND ST_Intersects(grid_cell.geometry, alpha.geometry)
			AND taxon_id IN :taxa""", {
				'taxa': tuple(taxa)
			})
	# Rows affected: 15721 (3.33s)

	run_sql(session, "Intersecting surveys with grid",
		"""CREATE TEMPORARY TABLE tmp_survey_grid
			(INDEX(grid_cell_id, survey_id))
			SELECT t2_survey.id AS survey_id, grid_cell.id AS grid_cell_id
			FROM t2_survey, grid_cell
			WHERE ST_Intersects(grid_cell.geometry, t2_survey.coords)""")
	# Rows affected: 1021487 (17.73s)

	run_sql(session, "Populate grid surveys",
		"""INSERT INTO t2_processed_survey (raw_survey_id, grid_cell_id, search_type_id, start_date_y, start_date_m, source_id, experimental_design_type_id)
			SELECT t2_survey.id, tmp_survey_grid.grid_cell_id, search_type_id, start_date_y, start_date_m, source_id, 2
			FROM t2_survey, tmp_survey_grid
			WHERE t2_survey.id = tmp_survey_grid.survey_id""")
	# 1021487 rows affected (17.10 sec)

	run_sql(session, "Populate presences / non-pseudo-absences",
		"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
			SELECT t2_processed_survey.id, t2_ultrataxon_sighting.taxon_id, count, unit_id, 0
			FROM t2_ultrataxon_sighting, t2_sighting, t2_processed_survey
			WHERE t2_ultrataxon_sighting.sighting_id = t2_sighting.id
			AND t2_sighting.survey_id = t2_processed_survey.raw_survey_id
			AND t2_processed_survey.experimental_design_type_id = 2
			AND t2_ultrataxon_sighting.taxon_id IN :taxa""", {
				'taxa': tuple(taxa)
			})
	# Rows affected: 6920 (3.24s)

	log.info("Populate pseudo-absences")
	for taxon_id in tqdm(taxa):
		session.execute(text("""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
				SELECT t2_processed_survey.id, tmp_taxon_grid.taxon_id, 0, 2, 1
				FROM t2_survey
				INNER JOIN tmp_survey_grid ON t2_survey.id = tmp_survey_grid.survey_id
				INNER JOIN t2_processed_survey ON t2_survey.id = t2_processed_survey.raw_survey_id AND t2_processed_survey.experimental_design_type_id = 2
				INNER JOIN tmp_taxon_grid ON tmp_survey_grid.grid_cell_id = tmp_taxon_grid.grid_cell_id AND taxon_id = :taxon_id
				LEFT JOIN t2_processed_sighting ON t2_processed_sighting.survey_id = t2_processed_survey.id AND t2_processed_sighting.taxon_id = tmp_taxon_grid.taxon_id
				WHERE t2_processed_sighting.id IS NULL"""), {
				'taxon_id': taxon_id
			})
	# Processed 23 taxa in 2m25s

def get_taxon_sites(taxon_id):
	session = get_session()
	try:
		return session.execute(text("""SELECT DISTINCT t2_survey_site.site_id, taxon_id
			FROM taxon_presence_alpha_hull_subdiv alpha STRAIGHT_JOIN t2_survey USE INDEX (coords), t2_survey_site
			WHERE ST_Contains(alpha.geometry, t2_survey.coords)
			AND t2_survey_site.survey_id = t2_survey.id
			AND taxon_id = :taxon_id
			AND alpha.range_id = 1"""), {
				'taxon_id': taxon_id
			}).fetchall()
	except:
		log.exception("Exception getting sites for taxon")
		raise
	finally:
		session.close()

def process_sites(session):
	run_sql(session, "Populate t2_survey_site",
		"""INSERT INTO t2_survey_site (survey_id, site_id)
			SELECT t2_survey.id, t2_site.id
			FROM t2_survey, t2_site
			WHERE site_id = t2_site.id""")
	# Query OK, 14073 rows affected (0.68 sec)
	# Records: 14073  Duplicates: 0  Warnings: 0

	session.commit()

	run_sql(session, "Populate t2_survey_site (spatial)",
		"""INSERT INTO t2_survey_site
			SELECT t2_survey.id, t2_site.id
			FROM t2_site STRAIGHT_JOIN t2_survey USE INDEX (coords)
			WHERE site_id IS NULL
			AND t2_survey.search_type_id = t2_site.search_type_id
			AND ST_Intersects(geometry, coords)""")
	# Query OK, 278678 rows affected (15.77 sec)
	# Records: 278678  Duplicates: 0  Warnings: 0

	session.commit()

	run_sql(session, "Populate standardised site surveys",
		"""INSERT INTO t2_processed_survey (raw_survey_id, site_id, search_type_id, start_date_y, start_date_m, source_id, experimental_design_type_id)
			SELECT t2_survey.id, t2_survey_site.site_id, search_type_id, start_date_y, start_date_m, source_id, 1
			FROM t2_survey, t2_survey_site
			WHERE t2_survey.id = t2_survey_site.survey_id""")
	# Query OK, 292751 rows affected (5.00 sec)
	# Records: 292751  Duplicates: 0  Warnings: 0

	session.commit()

	run_sql(session, "Populate presences / non-pseudo-absences",
		"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
			SELECT t2_processed_survey.id, t2_ultrataxon_sighting.taxon_id, count, unit_id, 0
			FROM t2_ultrataxon_sighting, t2_sighting, t2_processed_survey
			WHERE t2_ultrataxon_sighting.sighting_id = t2_sighting.id
			AND t2_sighting.survey_id = t2_processed_survey.raw_survey_id
			AND t2_processed_survey.experimental_design_type_id = 1""")
	# Query OK, 5775718 rows affected (2 min 35.55 sec)
	# Records: 5775718  Duplicates: 0  Warnings: 0

	session.commit()

	log.info("Identify taxa for each site based on alpha hulls")

	taxa = [taxon_id for (taxon_id,) in session.execute(text("SELECT DISTINCT taxon_id FROM taxon_presence_alpha_hull_subdiv WHERE taxon_id IN (SELECT taxon_id FROM processing_method WHERE data_type = 2)")).fetchall()]
	session.execute(text("""DROP TABLE IF EXISTS tmp_taxon_site"""))
	# Note for some reason CREATE TEMPORARY TABLE doesn't work as expected, the table seems to be empty by the time we get
	# to the next step... I'm guessing after some kind of timeout the transaction gets rolled back(?)
	session.execute(text("""CREATE TABLE tmp_taxon_site (
		site_id INT NOT NULL,
		taxon_id CHAR(6) NOT NULL,
		INDEX (taxon_id, site_id)
	)"""))

	# The next step was originally a very slow query, directly populating the tmp_taxon_site table.
	# Instead, I've broken the query down to process one taxon at a time
	# Furthermore, we process taxa in parallel threads to fully utilise the CPU, and then the results of the query are
	# inserted in bulk on the main thread.
	# Time taken: 17 min 4 s

	for result, error in tqdm(run_parallel(get_taxon_sites, taxa), total = len(taxa)):
		# Perform bulk insert on main thread
		if len(result) > 0:
			insert_data = [{ 'site_id': site_id, 'taxon_id': taxon_id } for site_id, taxon_id in result]
			session.execute(text("""INSERT INTO tmp_taxon_site (site_id, taxon_id) VALUES (:site_id, :taxon_id)"""), insert_data)
			session.commit()

	log.info("Generate pseudo absences")

	# This next step originally ran in about 15 minutes on my laptop as a single query, but took forever on the server
	# (I gave up after a couple of hours) so I've split it up by taxon with is a bit slower overall but at least you can
	# see progress

	# We store all pseudo absences in a temporary file and then write back to the database afterward
	# I tried a number of other approaches:
	#  - INSERT .. SELECT into table (too slow)
	#  - INSERT into temporary table, then INSERT .. SELECT into final table (too slow)
	#  - Store all pseudo absences in memory and then batch insert (too much memory usage)
	with tempfile.TemporaryFile(mode='r+') as temp:
		total_rows = 0
		for result, error in tqdm(run_parallel(get_pseudo_asbences, taxa), total = len(taxa)):
			if len(result):
				total_rows += len(result)
				temp.writelines(["%s,%s\n" % (survey_id, taxon_id) for survey_id, taxon_id in result])

		log.info("Insert pseudo absences")
		temp.seek(0)

		chunk_size = 10000
		for start in tqdm(range(0, total_rows, chunk_size)):
			chunk = [temp.readline().strip().split(",") for i in range(min(chunk_size, total_rows - start))]
			rows = [{ 'survey_id': survey_id, 'taxon_id': taxon_id } for survey_id, taxon_id in chunk]
			session.execute(text("""INSERT INTO t2_processed_sighting (survey_id, taxon_id, `count`, unit_id, pseudo_absence) VALUES (:survey_id, :taxon_id, 0, 2, 1)"""), rows)
			session.commit()


	session.execute(text("""DROP TABLE tmp_taxon_site"""))

def get_pseudo_asbences(taxon_id):
	session = get_session()
	# This query is a bit tricky. We do a left join to find taxa that are not present for a survey, and match on t2_processed_sighting.id = NULL to generate the pseudo-absences
	rows = session.execute(text("""
		SELECT t2_processed_survey.id, tmp_taxon_site.taxon_id
		FROM t2_survey
		INNER JOIN t2_survey_site ON t2_survey.id = t2_survey_site.survey_id
		INNER JOIN t2_processed_survey ON t2_survey.id = t2_processed_survey.raw_survey_id AND t2_processed_survey.experimental_design_type_id = 1
		INNER JOIN tmp_taxon_site ON t2_survey_site.site_id = tmp_taxon_site.site_id AND taxon_id = :taxon_id
		LEFT JOIN t2_processed_sighting ON t2_processed_sighting.survey_id = t2_processed_survey.id AND t2_processed_sighting.taxon_id = tmp_taxon_site.taxon_id
		WHERE t2_processed_sighting.id IS NULL"""), {
		'taxon_id': taxon_id
	}).fetchall()
	return [(survey_id, taxon_id) for survey_id, taxon_id in rows]

def run_sql(session, msg, sql, params = None):
	log.info(msg)
	t1 = time.time()
	r = session.execute(text(sql), params = params)
	t2 = time.time()
	log.info("  Rows affected: %s (%0.2fs)" % (r.rowcount, t2 - t1))

def is_empty(session, table):
	sql = "SELECT 1 FROM %s LIMIT 1" % table
	return len(session.execute(text(sql)).fetchall()) == 0


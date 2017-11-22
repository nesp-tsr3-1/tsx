from nesp.db import get_session
from tqdm import tqdm
import logging

log = logging.getLogger(__name__)

def process_database(commit = False):
	session = get_session()
	for title, sql in tqdm(_steps):
		log.info(title)
		session.execute(sql)

	if commit:
		log.info("Committing changes")
		session.commit()
	else:
		log.info("Rolling back changes (dry-run only)")
		session.rollback()

_steps = [(
	"Delete previous sightings",
	"""DELETE t2_processed_sighting
	FROM t2_processed_sighting, t2_processed_survey
	WHERE t2_processed_sighting.survey_id = t2_processed_survey.id
	AND t2_processed_survey.site_id IS NOT NULL"""
), (
	"Delete previous surveys",
	"""DELETE FROM t2_processed_survey
	WHERE t2_processed_survey.site_id IS NOT NULL"""
), (
	"Delete previous t2_survey_site entries",
	"""DELETE FROM t2_survey_site"""
), (
	"Populate t2_survey_site",
	"""INSERT INTO t2_survey_site (survey_id, site_id)
	SELECT t2_survey.id, t2_site.id
	FROM t2_survey, t2_site
	WHERE site_id = t2_site.id"""
	# Query OK, 14073 rows affected (0.68 sec)
	# Records: 14073  Duplicates: 0  Warnings: 0
), (
	"Populate t2_survey_site (spatial)",
	"""INSERT INTO t2_survey_site
	SELECT t2_survey.id, t2_site.id
	FROM t2_site STRAIGHT_JOIN t2_survey USE INDEX (coords)
	WHERE site_id IS NULL
	AND t2_survey.search_type_id = t2_site.search_type_id
	AND ST_Intersects(geometry, coords)"""
	# Query OK, 278678 rows affected (15.77 sec)
	# Records: 278678  Duplicates: 0  Warnings: 0
), (
	"Populate standardised site surveys",
	"""INSERT INTO t2_processed_survey (raw_survey_id, site_id, search_type_id, start_date_y, start_date_m, experimental_design_type_id)
	SELECT id, site_id, search_type_id, start_date_y, start_date_m, 1
	FROM t2_survey
	WHERE site_id IS NOT NULL"""
	# Query OK, 14073 rows affected (0.19 sec)
	# Records: 14073  Duplicates: 0  Warnings: 0
), (
	"Populate presences / non-pseudo-absences",
	"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
	SELECT t2_processed_survey.id, t2_ultrataxon_sighting.taxon_id, count, unit_id, 0
	FROM t2_ultrataxon_sighting, t2_sighting, t2_processed_survey
	WHERE t2_ultrataxon_sighting.sighting_id = t2_sighting.id
	AND t2_sighting.survey_id = t2_processed_survey.raw_survey_id
	AND t2_processed_survey.experimental_design_type_id = 1"""
	# Query OK, 213736 rows affected (3.41 sec)
	# Records: 213736  Duplicates: 0  Warnings: 0
), (
	"Identify taxa for each site based on alpha hulls",
	"""CREATE TEMPORARY TABLE tmp_taxon_site
	(INDEX (site_id), INDEX (taxon_id))
	SELECT DISTINCT t2_survey.site_id, taxon_id
	FROM t2_survey STRAIGHT_JOIN taxon_presence_alpha_hull_subdiv alpha USE INDEX (geometry)
	WHERE ST_Contains(alpha.geometry, t2_survey.coords)
	AND site_id IS NOT NULL
	AND alpha.range_id = 1"""
	# Query OK, 152448 rows affected (1 min 34.12 sec)
	# Records: 152448  Duplicates: 0  Warnings: 0
), (
	"Populate pseudo absences",
	# This query is a bit tricky. We do a left join to find taxons that are not present for a survey, and match on
	# t2_processed_sighting.id = NULL to generate the pseudo-absences
	"""INSERT INTO t2_processed_sighting (survey_id, taxon_id, count, unit_id, pseudo_absence)
	SELECT t2_processed_survey.id, tmp_taxon_site.taxon_id, 0, 2, 1
	FROM t2_survey
	INNER JOIN t2_processed_survey ON t2_survey.id = t2_processed_survey.raw_survey_id AND t2_processed_survey.experimental_design_type_id = 1
	INNER JOIN tmp_taxon_site ON t2_survey.site_id = tmp_taxon_site.site_id
	LEFT JOIN t2_processed_sighting ON survey_id = t2_processed_survey.id AND t2_processed_sighting.taxon_id = tmp_taxon_site.taxon_id
	WHERE t2_processed_sighting.id IS NULL"""
	# Query OK, 2606686 rows affected (31.70 sec)
	# Records: 2606686  Duplicates: 0  Warnings: 0
)]

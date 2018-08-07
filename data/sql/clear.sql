SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE taxon_presence_alpha_hull;
TRUNCATE taxon_presence_alpha_hull_subdiv;
TRUNCATE t2_ultrataxon_sighting;
TRUNCATE t2_processed_survey;
TRUNCATE t2_processed_sighting;
TRUNCATE t2_survey_site;
TRUNCATE aggregated_by_year;
TRUNCATE aggregated_by_month;

SET FOREIGN_KEY_CHECKS = 1;
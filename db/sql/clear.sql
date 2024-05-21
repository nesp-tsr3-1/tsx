# Clears out all derived data from the database

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE taxon_presence_alpha_hull;
TRUNCATE taxon_presence_alpha_hull_subdiv;
TRUNCATE aggregated_by_year;
TRUNCATE aggregated_by_month;

SET FOREIGN_KEY_CHECKS = 1;

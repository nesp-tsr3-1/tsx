# Unfortunately MySQL Workbench doesn't support spatial indexes so I'm creating them here instead

# MySQL 8 Requires SRID on geometry columns for spatial indexes to work
/*!80000 ALTER TABLE t2_survey MODIFY COLUMN coords POINT NOT NULL SRID 0 */;
/*!80000 ALTER TABLE taxon_presence_alpha_hull_subdiv MODIFY COLUMN geometry GEOMETRY NOT NULL SRID 0 */;
/*!80000 ALTER TABLE taxon_range_subdiv MODIFY COLUMN geometry MULTIPOLYGON NOT NULL SRID 0 */;
/*!80000 ALTER TABLE grid_cell MODIFY COLUMN geometry POLYGON NOT NULL SRID 0 */;
/*!80000 ALTER TABLE region_subdiv MODIFY COLUMN geometry MULTIPOLYGON NOT NULL SRID 0 */;

CREATE SPATIAL INDEX coords ON t2_survey (coords);
CREATE SPATIAL INDEX geometry ON taxon_presence_alpha_hull_subdiv (geometry);
CREATE SPATIAL INDEX geometry ON taxon_range_subdiv (geometry);
CREATE SPATIAL INDEX geometry ON grid_cell (geometry);
CREATE SPATIAL INDEX geometry ON region_subdiv (geometry);

INSERT INTO experimental_design_type (id, description) VALUES
(1, "Standardised site"),
(2, "Standardised grid"),
(3, "Unstandardised grid");

INSERT INTO response_variable_type (id, description) VALUES
(1, "Average count"),
(2, "Maximum count"),
(3, "Reporting rate");

INSERT INTO unit (id, description) VALUES
(1, "Sample: Occupancy (# presences/# absences)"),
(2, "Sample: abundance (counts)"),
(3, "Sample: density (counts/fixed areas)"),
(4, "Index"),
(5, "Proxy: recorded calls"),
(6, "Proxy: nests"),
(7, "Proxy: breeding pairs"),
(8, "Proxy: count of pre-fledging chicks"),
(9, "Sample: count of seen individuals after playback"),
(10, "Proxy: nests with eggs"),
(11, "Proxy: burrow estimate based on transect density");

INSERT INTO taxon_status (id, description) VALUES
(1, 'Least Concern'),
(2, 'Near Threatened'),
(3, 'Vulnerable'),
(4, 'Endangered'),
(5, 'Critically Endangered'),
(6, 'Critically Endangered (possibly extinct)'),
(7, 'Extinct');

INSERT INTO search_type (description) VALUES
('2ha 20 minute search'),
('500m Area search'),
('5km Area search'),
('Shorebird count area survey'),
('Breeding territory monitoring'),
('Incidental search'),
('Fixed route search'),
('Bird list'),
('Waterhole counts'),
('Aerial survey'),
('Roost counts'),
('Collected specimen'),
('VBA Bird transect'),
('VBA Breeding bird census'),
('VBA Helmeted Honeyeater survey'),
('VBA Listening'),
('VBA Mist net'),
('VBA Owl census'),
('VBA Plains-wanderer survey'),
('VBA Playback'),
('VBA Point spot count'),
('VBA Spotlighting'),
('VBA Spotlighting by area'),
('VBA Spotlighting on foot'),
('VBA Swift Parrot Survey'),
('VBA Targeted search'),
('VBA Timed bird census'),
('VBA Trap (unspecified)'),
('Unknown'),
('VBA Wetland count'),
('Estimation of annual breeding pairs by aerial photography and ground surveys'),
('Colony count'),
('Counting of birds seen after playback'),
('Slow walk (2-4km/h), listening to bird calls'),
('Annual flock count as flock flies to roosting area'),
('Direct observation at nest'),
('Search through feeding habitat patch'),
('4ha 20 minute search'),
('10 minute point count'),
('2ha non-20 minute search'),
('Automated call recordering'),
('LaTrobe Mallee call playback/spot counts');

INSERT INTO `range` (id, description) VALUES
  (1, "Core range"),
  (2, "Suspect"),
  (3, "Vagrant"),
  (4, "Historical"),
  (5, "Irruptive"),
  (6, "Introduced");

INSERT INTO `projection_name` VALUES
  ("GDA94", 4283),
  ("AGD66", 4202),
  ("AGD84", 4203),
  ("WSG84", 4326),
  ("AGD66 / AMG zone 48", 20248),
  ("AGD66 / AMG zone 49", 20249),
  ("AGD66 / AMG zone 50", 20250),
  ("AGD66 / AMG zone 51", 20251),
  ("AGD66 / AMG zone 52", 20252),
  ("AGD66 / AMG zone 53", 20253),
  ("AGD66 / AMG zone 54", 20254),
  ("AGD66 / AMG zone 55", 20255),
  ("AGD66 / AMG zone 56", 20256),
  ("AGD66 / AMG zone 57", 20257),
  ("AGD66 / AMG zone 58", 20258),
  ("AGD84 / AMG zone 48", 20348),
  ("AGD84 / AMG zone 49", 20349),
  ("AGD84 / AMG zone 50", 20350),
  ("AGD84 / AMG zone 51", 20351),
  ("AGD84 / AMG zone 52", 20352),
  ("AGD84 / AMG zone 53", 20353),
  ("AGD84 / AMG zone 54", 20354),
  ("AGD84 / AMG zone 55", 20355),
  ("AGD84 / AMG zone 56", 20356),
  ("AGD84 / AMG zone 57", 20357),
  ("AGD84 / AMG zone 58", 20358),
  ("GDA94 / MGA zone 48", 28348),
  ("GDA94 / MGA zone 49", 28349),
  ("GDA94 / MGA zone 50", 28350),
  ("GDA94 / MGA zone 51", 28351),
  ("GDA94 / MGA zone 52", 28352),
  ("GDA94 / MGA zone 53", 28353),
  ("GDA94 / MGA zone 54", 28354),
  ("GDA94 / MGA zone 55", 28355),
  ("GDA94 / MGA zone 56", 28356),
  ("GDA94 / MGA zone 57", 28357),
  ("GDA94 / MGA zone 58", 28358),
  ("GDA94 / Geoscience Australia Lambert", 3112),
  ("GDA94 / Australian Albers", 3577),
  ("Australia Albers Equal Area Conic	SR", 6642),
  ("AGD66 / Vicgrid66", 3110),
  ("GDA94 / Vicgrid94", 3111),
  ("GDA94 / SA Lambert", 3107),
  ("GDA94 / NSW Lambert", 3308),
  ("NSW AGD_1966_Lambert_Conformal_Conic	SR", 7316),
  ("ACT	SR", 7798),
  ("WGS 84 / Australian Antarctic Polar Stereographic", 3032),
  ("WGS 84 / Australian Antarctic Lambert", 3033),
  ("Australian Antarctic", 4176),
  ("Australian Antarctic (geocentric)", 4340),
  ("Cocos Islands 1965", 4708),
  ("Australian Antarctic (deg)", 61766405);

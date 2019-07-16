-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema nesp
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Table `unit`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `unit` ;

CREATE TABLE IF NOT EXISTS `unit` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `search_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `search_type` ;

CREATE TABLE IF NOT EXISTS `search_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `source_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `source_type` ;

CREATE TABLE IF NOT EXISTS `source_type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `source`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `source` ;

CREATE TABLE IF NOT EXISTS `source` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `source_type_id` INT NULL,
  `provider` TEXT NULL,
  `description` TEXT NULL,
  `notes` TEXT NULL,
  `authors` TEXT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_Source_SourceType_idx` (`source_type_id` ASC),
  CONSTRAINT `fk_Source_SourceType`
    FOREIGN KEY (`source_type_id`)
    REFERENCES `source_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `intensive_management`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `intensive_management` ;

CREATE TABLE IF NOT EXISTS `intensive_management` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t1_site`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t1_site` ;

CREATE TABLE IF NOT EXISTS `t1_site` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `source_id` INT NULL,
  `name` VARCHAR(255) NULL,
  `search_type_id` INT NOT NULL,
  `notes` TEXT NULL,
  `intensive_management_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_T1Site_Source1_idx` (`source_id` ASC),
  INDEX `fk_T1Site_SearchType1_idx` (`search_type_id` ASC),
  INDEX `fk_t1_site_intensive_management1_idx` (`intensive_management_id` ASC),
  CONSTRAINT `fk_T1Site_Source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T1Site_SearchType1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t1_site_intensive_management1`
    FOREIGN KEY (`intensive_management_id`)
    REFERENCES `intensive_management` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t1_survey`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t1_survey` ;

CREATE TABLE IF NOT EXISTS `t1_survey` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `site_id` INT NOT NULL,
  `source_id` INT NOT NULL,
  `source_primary_key` VARCHAR(255) NOT NULL,
  `start_date_d` SMALLINT NULL,
  `start_date_m` SMALLINT NULL,
  `start_date_y` SMALLINT NOT NULL,
  `finish_date_d` SMALLINT NULL,
  `finish_date_m` SMALLINT NULL,
  `finish_date_y` SMALLINT NULL,
  `start_time` TIME NULL,
  `finish_time` TIME NULL,
  `duration_in_minutes` INT NULL,
  `area_in_m2` DOUBLE NULL,
  `length_in_km` DOUBLE NULL,
  `number_of_traps_per_day` INT NULL,
  `coords` POINT NOT NULL,
  `location` TEXT NULL,
  `positional_accuracy_in_m` DOUBLE NULL,
  `comments` TEXT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_T1Survey_T1Site1_idx` (`site_id` ASC),
  INDEX `fk_T1Survey_Source1_idx` (`source_id` ASC),
  UNIQUE INDEX `source_primary_key_UNIQUE` (`source_primary_key` ASC),
  CONSTRAINT `fk_T1Survey_T1Site1`
    FOREIGN KEY (`site_id`)
    REFERENCES `t1_site` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T1Survey_Source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_level`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_level` ;

CREATE TABLE IF NOT EXISTS `taxon_level` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_status`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_status` ;

CREATE TABLE IF NOT EXISTS `taxon_status` (
  `id` INT NOT NULL,
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon` ;

CREATE TABLE IF NOT EXISTS `taxon` (
  `id` CHAR(8) NOT NULL,
  `ultrataxon` TINYINT(1) NOT NULL,
  `taxon_level_id` INT NULL,
  `spno` SMALLINT NULL,
  `common_name` VARCHAR(255) NULL,
  `scientific_name` VARCHAR(255) NOT NULL,
  `family_common_name` VARCHAR(255) NULL,
  `family_scientific_name` VARCHAR(255) NULL,
  `order` VARCHAR(255) NULL,
  `population` VARCHAR(255) NULL,
  `epbc_status_id` INT NULL,
  `iucn_status_id` INT NULL,
  `state_status_id` INT NULL,
  `max_status_id` INT GENERATED ALWAYS AS (NULLIF(GREATEST(COALESCE(taxon.epbc_status_id, 0), COALESCE(taxon.iucn_status_id, 0), COALESCE(taxon.state_status_id, 0)), 0)),
  `national_priority` TINYINT(1) NOT NULL DEFAULT 0,
  `taxonomic_group` VARCHAR(255) NOT NULL,
  `suppress_spatial_representativeness` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `fk_Taxon_TaxonLevel1_idx` (`taxon_level_id` ASC),
  INDEX `fk_taxon_taxon_status2_idx` (`epbc_status_id` ASC),
  INDEX `fk_taxon_taxon_status3_idx` (`iucn_status_id` ASC),
  INDEX `fk_taxon_taxon_status4_idx` (`state_status_id` ASC),
  CONSTRAINT `fk_Taxon_TaxonLevel1`
    FOREIGN KEY (`taxon_level_id`)
    REFERENCES `taxon_level` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_taxon_status2`
    FOREIGN KEY (`epbc_status_id`)
    REFERENCES `taxon_status` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_taxon_status3`
    FOREIGN KEY (`iucn_status_id`)
    REFERENCES `taxon_status` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_taxon_status4`
    FOREIGN KEY (`state_status_id`)
    REFERENCES `taxon_status` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_hybrid`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_hybrid` ;

CREATE TABLE IF NOT EXISTS `taxon_hybrid` (
  `id` CHAR(12) NOT NULL COMMENT 'e.g. u123a.b.c',
  `taxon_id` CHAR(8) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_TaxonHybrid_Taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_TaxonHybrid_Taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t1_sighting`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t1_sighting` ;

CREATE TABLE IF NOT EXISTS `t1_sighting` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `survey_id` INT NOT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `count` DOUBLE NOT NULL,
  `unit_id` INT NOT NULL,
  `breeding` TINYINT(1) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_T1Sighting_T1Survey1_idx` (`survey_id` ASC),
  INDEX `fk_T1Sighting_Taxon1_idx` (`taxon_id` ASC),
  INDEX `fk_T1Sighting_Unit1_idx` (`unit_id` ASC),
  CONSTRAINT `fk_T1Sighting_T1Survey1`
    FOREIGN KEY (`survey_id`)
    REFERENCES `t1_survey` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T1Sighting_Taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T1Sighting_Unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `incidental_sighting`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `incidental_sighting` ;

CREATE TABLE IF NOT EXISTS `incidental_sighting` (
  `taxon_id` CHAR(8) NOT NULL,
  `coords` POINT NULL,
  `date` DATE NULL,
  INDEX `fk_incidental_sighting_taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_incidental_sighting_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_site`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_site` ;

CREATE TABLE IF NOT EXISTS `t2_site` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `source_id` INT NULL,
  `name` VARCHAR(255) NULL,
  `search_type_id` INT NOT NULL,
  `geometry` MULTIPOLYGON NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_t2_site_search_type1_idx` (`search_type_id` ASC),
  INDEX `fk_t2_site_source1_idx` (`source_id` ASC),
  INDEX `source_name` (`source_id` ASC, `name` ASC),
  CONSTRAINT `fk_t2_site_search_type1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_site_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_survey`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_survey` ;

CREATE TABLE IF NOT EXISTS `t2_survey` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `site_id` INT NULL,
  `source_id` INT NOT NULL,
  `start_date_d` SMALLINT NULL,
  `start_date_m` SMALLINT NULL,
  `start_date_y` SMALLINT NOT NULL,
  `finish_date_d` SMALLINT NULL,
  `finish_date_m` SMALLINT NULL,
  `finish_date_y` SMALLINT NULL,
  `start_time` TIME NULL,
  `finish_time` TIME NULL,
  `duration_in_minutes` INT NULL,
  `area_in_m2` DOUBLE NULL,
  `length_in_km` DOUBLE NULL,
  `coords` POINT NOT NULL,
  `location` TEXT NULL,
  `positional_accuracy_in_m` DOUBLE NULL,
  `comments` TEXT NULL,
  `search_type_id` INT NOT NULL,
  `source_primary_key` VARCHAR(255) NOT NULL,
  `secondary_source_id` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_T1Survey_Source1_idx` (`source_id` ASC),
  INDEX `fk_T2Survey_SearchType1_idx` (`search_type_id` ASC),
  UNIQUE INDEX `source_primary_key_UNIQUE` (`source_primary_key` ASC),
  INDEX `fk_t2_survey_t2_site1_idx` (`site_id` ASC),
  CONSTRAINT `fk_T1Survey_Source10`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2Survey_SearchType1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_survey_t2_site1`
    FOREIGN KEY (`site_id`)
    REFERENCES `t2_site` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_survey_site`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_survey_site` ;

CREATE TABLE IF NOT EXISTS `t2_survey_site` (
  `survey_id` INT NOT NULL,
  `site_id` INT NOT NULL,
  INDEX `fk_T2SurveySite_T2Site1_idx` (`site_id` ASC),
  PRIMARY KEY (`survey_id`, `site_id`),
  CONSTRAINT `fk_T2SurveySite_T2Survey1`
    FOREIGN KEY (`survey_id`)
    REFERENCES `t2_survey` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2SurveySite_T2Site1`
    FOREIGN KEY (`site_id`)
    REFERENCES `t2_site` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_sighting`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_sighting` ;

CREATE TABLE IF NOT EXISTS `t2_sighting` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `survey_id` INT NOT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `count` DOUBLE NULL,
  `unit_id` INT NULL,
  `breeding` TINYINT(1) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_T2Sighting_T2Survey1_idx` (`survey_id` ASC),
  INDEX `fk_T2Sighting_Unit1_idx` (`unit_id` ASC),
  INDEX `fk_T2Sighting_Taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_T2Sighting_T2Survey1`
    FOREIGN KEY (`survey_id`)
    REFERENCES `t2_survey` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2Sighting_Unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2Sighting_Taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `range`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `range` ;

CREATE TABLE IF NOT EXISTS `range` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_ultrataxon_sighting`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_ultrataxon_sighting` ;

CREATE TABLE IF NOT EXISTS `t2_ultrataxon_sighting` (
  `sighting_id` INT NOT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `range_id` INT NOT NULL,
  `generated_subspecies` TINYINT(1) NOT NULL,
  INDEX `fk_T2SightingRangeType_RangeType1_idx` (`range_id` ASC),
  PRIMARY KEY (`sighting_id`, `taxon_id`),
  INDEX `fk_T2ProcessedSighting_Taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_T2SightingRangeType_RangeType1`
    FOREIGN KEY (`range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2ProcessedSighting_T2Sighting1`
    FOREIGN KEY (`sighting_id`)
    REFERENCES `t2_sighting` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_T2ProcessedSighting_Taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_presence_alpha_hull`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_presence_alpha_hull` ;

CREATE TABLE IF NOT EXISTS `taxon_presence_alpha_hull` (
  `taxon_id` CHAR(8) NOT NULL,
  `range_id` INT NOT NULL,
  `breeding_range_id` INT NULL,
  `geometry` GEOMETRY NOT NULL,
  INDEX `fk_taxon_presence_alpha_hull_range1_idx` (`range_id` ASC),
  CONSTRAINT `fk_taxon_presence_alpha_hull_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_presence_alpha_hull_range1`
    FOREIGN KEY (`range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `grid_cell`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `grid_cell` ;

CREATE TABLE IF NOT EXISTS `grid_cell` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `geometry` POLYGON NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_processed_survey`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_processed_survey` ;

CREATE TABLE IF NOT EXISTS `t2_processed_survey` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `raw_survey_id` INT NOT NULL,
  `site_id` INT NULL,
  `grid_cell_id` INT NULL,
  `search_type_id` INT NOT NULL,
  `start_date_y` SMALLINT NOT NULL,
  `start_date_m` SMALLINT NULL,
  `source_id` INT NOT NULL,
  `experimental_design_type_id` INT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_t2_processed_survey_t2_survey1_idx` (`raw_survey_id` ASC),
  INDEX `fk_t2_processed_survey_t2_site1_idx` (`site_id` ASC),
  INDEX `fk_t2_processed_survey_grid_cell1_idx` (`grid_cell_id` ASC),
  INDEX `fk_t2_processed_survey_source1_idx` (`source_id` ASC),
  CONSTRAINT `fk_t2_processed_survey_t2_survey1`
    FOREIGN KEY (`raw_survey_id`)
    REFERENCES `t2_survey` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_processed_survey_t2_site1`
    FOREIGN KEY (`site_id`)
    REFERENCES `t2_site` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_processed_survey_grid_cell1`
    FOREIGN KEY (`grid_cell_id`)
    REFERENCES `grid_cell` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_processed_survey_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `response_variable_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `response_variable_type` ;

CREATE TABLE IF NOT EXISTS `response_variable_type` (
  `id` INT NOT NULL,
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `state`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `state` ;

CREATE TABLE IF NOT EXISTS `state` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NULL,
  `geometry` MULTIPOLYGON NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `region`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `region` ;

CREATE TABLE IF NOT EXISTS `region` (
  `id` INT NOT NULL,
  `name` VARCHAR(255) NULL,
  `geometry` MULTIPOLYGON NOT NULL,
  `state` VARCHAR(255) NULL,
  `positional_accuracy_in_m` INT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `species_range`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `species_range` ;

CREATE TABLE IF NOT EXISTS `species_range` (
  `species_id` INT NOT NULL,
  PRIMARY KEY (`species_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_range`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_range` ;

CREATE TABLE IF NOT EXISTS `taxon_range` (
  `taxon_id` CHAR(8) NOT NULL,
  `range_id` INT NOT NULL,
  `breeding_range_id` INT NULL,
  `geometry` MULTIPOLYGON NOT NULL,
  INDEX `fk_taxon_range_range1_idx` (`range_id` ASC),
  INDEX `fk_taxon_range_range2_idx` (`breeding_range_id` ASC),
  INDEX `fk_taxon_range_taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_taxon_range_range1`
    FOREIGN KEY (`range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_range_range2`
    FOREIGN KEY (`breeding_range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_range_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_range_subdiv`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_range_subdiv` ;

CREATE TABLE IF NOT EXISTS `taxon_range_subdiv` (
  `taxon_id` CHAR(8) NOT NULL,
  `range_id` INT NOT NULL,
  `breeding_range_id` INT NULL,
  `geometry` MULTIPOLYGON NOT NULL,
  INDEX `fk_taxon_range_range1_idx` (`range_id` ASC),
  INDEX `fk_taxon_range_range2_idx` (`breeding_range_id` ASC),
  INDEX `fk_taxon_range_taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_taxon_range_range10`
    FOREIGN KEY (`range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_range_range20`
    FOREIGN KEY (`breeding_range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_range_taxon10`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_presence_alpha_hull_subdiv`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_presence_alpha_hull_subdiv` ;

CREATE TABLE IF NOT EXISTS `taxon_presence_alpha_hull_subdiv` (
  `taxon_id` CHAR(8) NOT NULL,
  `range_id` INT NOT NULL,
  `breeding_range_id` INT NULL,
  `geometry` GEOMETRY NOT NULL,
  INDEX `fk_taxon_presence_alpha_hull_range1_idx` (`range_id` ASC),
  CONSTRAINT `fk_taxon_presence_alpha_hull_taxon10`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_taxon_presence_alpha_hull_range10`
    FOREIGN KEY (`range_id`)
    REFERENCES `range` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `t2_processed_sighting`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `t2_processed_sighting` ;

CREATE TABLE IF NOT EXISTS `t2_processed_sighting` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `survey_id` INT NOT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `count` DOUBLE NOT NULL,
  `unit_id` INT NOT NULL,
  `pseudo_absence` TINYINT(1) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `survey_id_taxon_id` (`survey_id` ASC, `taxon_id` ASC),
  INDEX `fk_t2_processed_sighting_unit1_idx` (`unit_id` ASC),
  INDEX `fk_t2_processed_sighting_taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_t2_processed_sighting_unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_processed_sighting_t2_processed_survey1`
    FOREIGN KEY (`survey_id`)
    REFERENCES `t2_processed_survey` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_t2_processed_sighting_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `experimental_design_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `experimental_design_type` ;

CREATE TABLE IF NOT EXISTS `experimental_design_type` (
  `id` INT NOT NULL,
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `aggregated_by_month`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `aggregated_by_month` ;

CREATE TABLE IF NOT EXISTS `aggregated_by_month` (
  `start_date_y` SMALLINT NOT NULL,
  `start_date_m` SMALLINT NULL,
  `site_id` INT NULL,
  `grid_cell_id` INT NULL,
  `search_type_id` INT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `experimental_design_type_id` INT NOT NULL,
  `response_variable_type_id` INT NOT NULL,
  `value` DOUBLE NOT NULL,
  `data_type` INT NOT NULL,
  `source_id` INT NOT NULL,
  `region_id` INT NULL,
  `unit_id` INT NOT NULL,
  `positional_accuracy_in_m` DOUBLE NULL,
  `centroid_coords` POINT NOT NULL,
  `survey_count` INT NOT NULL,
  `time_series_id` VARCHAR(32) GENERATED ALWAYS AS (CONCAT(source_id, '_', unit_id, '_', COALESCE(search_type_id, '0'), '_', COALESCE(site_id, CONCAT('g', grid_cell_id)), '_', taxon_id)),
  INDEX `fk_aggregated_by_month_grid_cell1_idx` (`grid_cell_id` ASC),
  INDEX `fk_aggregated_by_month_search_type1_idx` (`search_type_id` ASC),
  INDEX `fk_aggregated_by_month_taxon1_idx` (`taxon_id` ASC),
  INDEX `fk_aggregated_by_month_source1_idx` (`source_id` ASC),
  INDEX `fk_aggregated_by_month_experimental_design_type1_idx` (`experimental_design_type_id` ASC),
  INDEX `fk_aggregated_by_month_response_variable_type1_idx` (`response_variable_type_id` ASC),
  INDEX `fk_aggregated_by_month_unit1_idx` (`unit_id` ASC),
  INDEX `fk_aggregated_by_month_region1_idx` (`region_id` ASC),
  CONSTRAINT `fk_aggregated_by_month_grid_cell1`
    FOREIGN KEY (`grid_cell_id`)
    REFERENCES `grid_cell` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_search_type1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_experimental_design_type1`
    FOREIGN KEY (`experimental_design_type_id`)
    REFERENCES `experimental_design_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_response_variable_type1`
    FOREIGN KEY (`response_variable_type_id`)
    REFERENCES `response_variable_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_month_region1`
    FOREIGN KEY (`region_id`)
    REFERENCES `region` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `aggregated_by_year`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `aggregated_by_year` ;

CREATE TABLE IF NOT EXISTS `aggregated_by_year` (
  `start_date_y` SMALLINT NOT NULL,
  `site_id` INT NULL,
  `grid_cell_id` INT NULL,
  `search_type_id` INT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `experimental_design_type_id` INT NOT NULL,
  `response_variable_type_id` INT NOT NULL,
  `value` DOUBLE NOT NULL,
  `data_type` INT NOT NULL,
  `source_id` INT NOT NULL,
  `region_id` INT NULL,
  `unit_id` INT NOT NULL,
  `positional_accuracy_in_m` DOUBLE NULL,
  `centroid_coords` POINT NOT NULL,
  `survey_count` INT NOT NULL,
  `time_series_id` VARCHAR(32) GENERATED ALWAYS AS (CONCAT(source_id, '_', unit_id, '_', COALESCE(search_type_id, '0'), '_', COALESCE(site_id, CONCAT('g', grid_cell_id)), '_', taxon_id)),
  `include_in_analysis` TINYINT(1) NOT NULL DEFAULT 0,
  INDEX `fk_aggregated_by_year_grid_cell1_idx` (`grid_cell_id` ASC),
  INDEX `fk_aggregated_by_year_search_type1_idx` (`search_type_id` ASC),
  INDEX `fk_aggregated_by_year_taxon1_idx` (`taxon_id` ASC),
  INDEX `fk_aggregated_by_year_source1_idx` (`source_id` ASC),
  INDEX `fk_aggregated_by_year_experimental_design_type1_idx` (`experimental_design_type_id` ASC),
  INDEX `fk_aggregated_by_year_response_variable_type1_idx` (`response_variable_type_id` ASC),
  INDEX `fk_aggregated_by_year_unit1_idx` (`unit_id` ASC),
  INDEX `fk_aggregated_by_year_region1_idx` (`region_id` ASC),
  CONSTRAINT `fk_aggregated_by_year_grid_cell1`
    FOREIGN KEY (`grid_cell_id`)
    REFERENCES `grid_cell` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_search_type1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_experimental_design_type1`
    FOREIGN KEY (`experimental_design_type_id`)
    REFERENCES `experimental_design_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_response_variable_type1`
    FOREIGN KEY (`response_variable_type_id`)
    REFERENCES `response_variable_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_aggregated_by_year_region1`
    FOREIGN KEY (`region_id`)
    REFERENCES `region` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `region_subdiv`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `region_subdiv` ;

CREATE TABLE IF NOT EXISTS `region_subdiv` (
  `id` INT NOT NULL,
  `name` VARCHAR(255) NULL,
  `geometry` MULTIPOLYGON NOT NULL)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `processing_method`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `processing_method` ;

CREATE TABLE IF NOT EXISTS `processing_method` (
  `taxon_id` CHAR(8) NOT NULL,
  `unit_id` INT NULL,
  `source_id` INT NOT NULL,
  `search_type_id` INT NULL,
  `data_type` INT NOT NULL,
  `response_variable_type_id` INT NOT NULL,
  `experimental_design_type_id` INT NOT NULL,
  `positional_accuracy_threshold_in_m` DOUBLE NULL,
  INDEX `fk_processing_method_unit1_idx` (`unit_id` ASC),
  INDEX `fk_processing_method_source1_idx` (`source_id` ASC),
  INDEX `fk_processing_method_search_type1_idx` (`search_type_id` ASC),
  UNIQUE INDEX `uniq` (`taxon_id` ASC, `unit_id` ASC, `source_id` ASC, `search_type_id` ASC, `data_type` ASC),
  CONSTRAINT `fk_processing_method_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_processing_method_unit1`
    FOREIGN KEY (`unit_id`)
    REFERENCES `unit` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_processing_method_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_processing_method_search_type1`
    FOREIGN KEY (`search_type_id`)
    REFERENCES `search_type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_source_alpha_hull`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_source_alpha_hull` ;

CREATE TABLE IF NOT EXISTS `taxon_source_alpha_hull` (
  `taxon_id` CHAR(8) NOT NULL,
  `source_id` INT NOT NULL,
  `data_type` VARCHAR(255) NOT NULL,
  `geometry` MULTIPOLYGON NULL,
  `core_range_area_in_m2` DOUBLE NOT NULL,
  `alpha_hull_area_in_m2` DOUBLE NULL,
  PRIMARY KEY (`taxon_id`, `source_id`, `data_type`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_source`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_source` ;

CREATE TABLE IF NOT EXISTS `data_source` (
  `source_id` INT NOT NULL,
  `taxon_id` CHAR(8) NOT NULL,
  `data_agreement_id` INT NULL,
  `objective_of_monitoring_id` INT NULL,
  `absences_recorded` TINYINT(1) NULL,
  `standardisation_of_method_effort_id` INT NULL,
  `consistency_of_monitoring_id` INT NULL,
  `exclude_from_analysis` TINYINT(1) NOT NULL,
  `start_year` INT(4) NULL,
  `end_year` INT(4) NULL,
  `suppress_aggregated_data` TINYINT(1) NOT NULL,
  PRIMARY KEY (`source_id`, `taxon_id`),
  INDEX `fk_data_source_taxon1_idx` (`taxon_id` ASC),
  CONSTRAINT `fk_data_source_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_data_source_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `time_series`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `time_series` ;

CREATE TABLE IF NOT EXISTS `time_series` (
  `id` VARCHAR(32) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projection_name`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `projection_name` ;

CREATE TABLE IF NOT EXISTS `projection_name` (
  `name` VARCHAR(64) NOT NULL,
  `epsg_srid` INT NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `taxon_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `taxon_group` ;

CREATE TABLE IF NOT EXISTS `taxon_group` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `taxon_id` CHAR(8) NOT NULL,
  `group_name` VARCHAR(255) NOT NULL,
  `subgroup_name` VARCHAR(255) NULL,
  INDEX `fk_taxon_group_taxon1_idx` (`taxon_id` ASC),
  UNIQUE INDEX `taxon_group_subgroup` (`taxon_id` ASC, `group_name` ASC, `subgroup_name` ASC),
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_taxon_group_taxon1`
    FOREIGN KEY (`taxon_id`)
    REFERENCES `taxon` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user` ;

CREATE TABLE IF NOT EXISTS `user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NULL COMMENT '	',
  `password_hash` TEXT NULL,
  `first_name` TEXT NULL,
  `last_name` TEXT NULL,
  `phone_number` VARCHAR(32) NULL,
  `password_reset_code` VARCHAR(32) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role` ;

CREATE TABLE IF NOT EXISTS `role` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`description` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user_role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_role` ;

CREATE TABLE IF NOT EXISTS `user_role` (
  `user_id` INT NOT NULL,
  `role_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`),
  INDEX `fk_user_role_role1_idx` (`role_id` ASC),
  CONSTRAINT `fk_user_role_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_role_role1`
    FOREIGN KEY (`role_id`)
    REFERENCES `role` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `user_source`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_source` ;

CREATE TABLE IF NOT EXISTS `user_source` (
  `user_id` INT NOT NULL,
  `source_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `source_id`),
  INDEX `fk_user_source_source1_idx` (`source_id` ASC),
  CONSTRAINT `fk_user_source_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_source_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_import_status`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_import_status` ;

CREATE TABLE IF NOT EXISTS `data_import_status` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_import`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_import` ;

CREATE TABLE IF NOT EXISTS `data_import` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `source_id` INT NULL,
  `status_id` INT NULL,
  `upload_uuid` VARCHAR(36) NULL,
  `filename` TEXT NULL,
  `error_count` INT NULL,
  `warning_count` INT NULL,
  `data_type` INT NOT NULL,
  `time_created` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` INT NULL,
  `source_desc` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_data_import_source1_idx` (`source_id` ASC),
  INDEX `fk_data_import_data_import_status1_idx` (`status_id` ASC),
  INDEX `fk_data_import_user1_idx` (`user_id` ASC),
  CONSTRAINT `fk_data_import_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_data_import_data_import_status1`
    FOREIGN KEY (`status_id`)
    REFERENCES `data_import_status` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_data_import_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `data_processing_notes`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `data_processing_notes` ;

CREATE TABLE IF NOT EXISTS `data_processing_notes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `source_id` INT NOT NULL,
  `time_created` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `notes` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_data_processing_notes_user1_idx` (`user_id` ASC),
  INDEX `fk_data_processing_notes_source1_idx` (`source_id` ASC),
  CONSTRAINT `fk_data_processing_notes_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_data_processing_notes_source1`
    FOREIGN KEY (`source_id`)
    REFERENCES `source` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

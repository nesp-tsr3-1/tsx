import duckdb
from tsx.db.connect import get_database_duckdb_attach_string, get_session
from tsx.config import data_dir
import os
from tqdm import tqdm
from sqlalchemy import text

def main():
    session = get_session()
    source_ids = session.execute(text("SELECT id FROM source")).fetchall()

    # Prepare database (using a file seems to be more stable on Duckdb 1.4.4)
    filename = '/tmp/tsx_preprocessing.duckdb'
    try:
        os.remove(filename)
    except OSError:
        pass

    db = duckdb.connect(filename)
    db.sql("LOAD mysql")
    db.sql("INSTALL spatial")
    db.sql("LOAD spatial")
    db.sql("ATTACH '%s' AS mysqldb (TYPE mysql)" % get_database_duckdb_attach_string())
    db.sql("CREATE SEQUENCE serial")

    db.sql("""CREATE TABLE region AS
        SELECT id, name, state, ST_GeomFromText(geom_wkt) AS geom, lat, lon
        FROM mysql_query('mysqldb', 'SELECT
            id, name, state,
            ST_AsWKT(geometry) AS geom_wkt,
            ST_Y(ST_Centroid(geometry)) AS lat,
            ST_X(ST_Centroid(geometry)) AS lon
        FROM region')
    """)
    db.sql("""CREATE INDEX region_idx ON region USING RTREE (geom)""")

    for (source_id,) in tqdm(source_ids):
        preprocess_data(source_id, db)

    os.remove(filename)

def preprocess_data(source_id, db):
    sql1 = f"""
        SELECT
            CONCAT(source.id, '_', t1_sighting.unit_id, '_', COALESCE(t1_site.search_type_id, '0'), '_', t1_site.id, '_', taxon.id) AS TimeSeriesID,
            t1_survey.id AS SurveyID,
            t1_sighting.id AS SightingID,
            1 AS DataType,
            (SELECT description FROM source_type WHERE id = source.source_type_id) AS SourceType,
            taxon.eligible_for_tsx AS EligibleForTSX,
            taxon.taxonomic_group AS TaxonomicGroup,
            (SELECT description FROM taxon_status WHERE id = epbc_status_id) AS EPBCStatus,
            (SELECT description FROM taxon_status WHERE id = iucn_status_id) AS IUCNStatus,
            (SELECT description FROM taxon_status WHERE id = bird_action_plan_status_id) AS BirdActionPlanStatus,
            (SELECT description FROM taxon_status WHERE id = max_status_id) AS MaxStatus,
            source.id AS SourceID,
            source.description AS SourceDesc,
            source.provider AS SourceProvider,
            COALESCE((SELECT description FROM data_processing_type WHERE id = source.data_processing_type_id), "N/A") AS DataProcessingType,
            t1_survey.location AS LocationName,
            (SELECT description FROM search_type WHERE id = t1_site.search_type_id) AS SearchTypeDesc,
            t1_survey.source_primary_key AS SourcePrimaryKey,
            start_date_m AS StartMonth,
            start_date_y AS StartYear,
            CONCAT(
                LPAD(COALESCE(start_date_d, 0), 2, 0), '/',
                LPAD(COALESCE(start_date_m, 0), 2, 0), '/',
                start_date_y
            ) AS StartDate,
            COALESCE(CONCAT(
                LPAD(COALESCE(finish_date_d, 0), 2, 0), '/',
                LPAD(COALESCE(finish_date_m, 0), 2, 0), '/',
                finish_date_y
            ), "N/A") AS FinishDate,
            TIME_FORMAT(start_time, "%H:%i") AS StartTime,
            TIME_FORMAT(finish_time, "%H:%i") AS FinishTime,
            CASE WHEN t1_survey.duration_in_minutes < 24 * 60 * 60 THEN
                t1_survey.duration_in_minutes
                ELSE ''
            END AS DurationInMinutes,
            CASE
                WHEN t1_survey.duration_in_minutes >= 24 * 60 * 60 THEN t1_survey.duration_in_minutes / 24 * 60 * 60
                ELSE ''
            END AS `DurationInDays/Nights`,
            t1_survey.number_of_traps_per_day AS `NumberOfTrapsPerDay/Night`,
            t1_survey.area_in_m2 AS `AreaInM2`,
            t1_survey.length_in_km AS LengthInKm,
            t1_site.id AS SiteID,
            t1_site.name AS SiteName,
            ST_Y(t1_survey.coords) as Y,
            ST_X(t1_survey.coords) as X,
            'EPSG:4326' AS ProjectionReference,
            t1_survey.positional_accuracy_in_m AS PositionalAccuracyInM,
            # '' AS State,
            # '' AS Region,
            # CAST(NULL AS DOUBLE) AS RegionCentroidLongitude,
            # CAST(NULL AS DOUBLE) AS RegionCentroidLatitude,
            t1_survey.comments AS SurveyComments,
            (SELECT description FROM monitoring_program WHERE id = source.monitoring_program_id) AS MonitoringProgram,
            source.monitoring_program_comments AS MonitoringProgramComments,
            COALESCE((SELECT type FROM management WHERE id = t1_site.management_id), "No known management") AS Management,
            COALESCE((SELECT description FROM management WHERE id = t1_site.management_id), "Unknown") AS ManagementCategory,
            t1_site.management_comments AS ManagementCategoryComments,
            t1_sighting.taxon_id AS TaxonID,
            taxon.common_name AS CommonName,
            taxon.`order` AS `Order`,
            taxon.scientific_name AS ScientificName,
            taxon.family_scientific_name AS Family,
            taxon.family_common_name AS FamilyCommonName,
            CASE taxon.taxonomic_group
                WHEN 'Birds' THEN 'Aves'
                WHEN 'Mammals' THEN 'Mammalia'
                ELSE ''
            END AS Class,
            t1_sighting.`count` AS Count,
            (SELECT description FROM unit WHERE id = t1_sighting.unit_id) AS UnitOfMeasurement,
            COALESCE((SELECT description FROM unit_type WHERE id = t1_sighting.unit_type_id), "N/A") AS UnitType,
            t1_sighting.comments AS SightingComments
        FROM t1_survey
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        WHERE source.id = {source_id}
    """

    sql2 = f"""
        SELECT
            '' AS TimeSeriesID,
            t2_survey.id AS SurveyID,
            t2_sighting.id AS SightingID,
            2 AS DataType,
            (SELECT description FROM source_type WHERE id = source.source_type_id) AS SourceType,
            taxon.eligible_for_tsx AS EligibleForTSX,
            taxon.taxonomic_group AS TaxonomicGroup,
            (SELECT description FROM taxon_status WHERE id = epbc_status_id) AS EPBCStatus,
            (SELECT description FROM taxon_status WHERE id = iucn_status_id) AS IUCNStatus,
            (SELECT description FROM taxon_status WHERE id = bird_action_plan_status_id) AS BirdActionPlanStatus,
            (SELECT description FROM taxon_status WHERE id = max_status_id) AS MaxStatus,
            source.id AS SourceID,
            source.description AS SourceDesc,
            source.provider AS SourceProvider,
            COALESCE((SELECT description FROM data_processing_type WHERE id = source.data_processing_type_id), "N/A") AS DataProcessingType,
            t2_survey.location AS LocationName,
            (SELECT description FROM search_type WHERE id = t2_survey.search_type_id) AS SearchTypeDesc,
            t2_survey.source_primary_key AS SourcePrimaryKey,
            start_date_m AS StartMonth,
            start_date_y AS StartYear,
            CONCAT(
                LPAD(COALESCE(start_date_d, 0), 2, 0), '/',
                LPAD(COALESCE(start_date_m, 0), 2, 0), '/',
                start_date_y
            ) AS StartDate,
            COALESCE(CONCAT(
                LPAD(COALESCE(finish_date_d, 0), 2, 0), '/',
                LPAD(COALESCE(finish_date_m, 0), 2, 0), '/',
                finish_date_y
            ), "N/A") AS FinishDate,
            TIME_FORMAT(start_time, "%H:%i") AS StartTime,
            TIME_FORMAT(finish_time, "%H:%i") AS FinishTime,
            CASE WHEN t2_survey.duration_in_minutes < 24 * 60 * 60 THEN
                t2_survey.duration_in_minutes
                ELSE ''
            END AS DurationInMinutes,
            CASE
                WHEN t2_survey.duration_in_minutes >= 24 * 60 * 60 THEN t2_survey.duration_in_minutes / 24 * 60 * 60
                ELSE ''
            END AS `DurationInDays/Nights`,
            NULL AS `NumberOfTrapsPerDay/Night`,
            t2_survey.area_in_m2 AS `AreaInM2`,
            t2_survey.length_in_km AS LengthInKm,
            t2_site.id AS SiteID,
            t2_site.name AS SiteName,
            ST_Y(t2_survey.coords) as Y,
            ST_X(t2_survey.coords) as X,
            'EPSG:4326' AS ProjectionReference,
            t2_survey.positional_accuracy_in_m AS PositionalAccuracyInM,
            # '' AS State,
            # '' AS Region,
            # CAST(NULL AS DOUBLE) AS RegionCentroidLongitude,
            # CAST(NULL AS DOUBLE) AS RegionCentroidLatitude,
            t2_survey.comments AS SurveyComments,
            (SELECT description FROM monitoring_program WHERE id = source.monitoring_program_id) AS MonitoringProgram,
            source.monitoring_program_comments AS MonitoringProgramComments,
            "No known management" AS Management,
            "Unknown" AS ManagementCategory,
            NULL AS ManagementCategoryComments,
            t2_sighting.taxon_id AS TaxonID,
            taxon.common_name AS CommonName,
            taxon.`order` AS `Order`,
            taxon.scientific_name AS ScientificName,
            taxon.family_scientific_name AS Family,
            taxon.family_common_name AS FamilyCommonName,
            CASE taxon.taxonomic_group
                WHEN 'Birds' THEN 'Aves'
                WHEN 'Mammals' THEN 'Mammalia'
                ELSE ''
            END AS Class,
            t2_sighting.`count` AS Count,
            (SELECT description FROM unit WHERE id = t2_sighting.unit_id) AS UnitOfMeasurement,
            COALESCE((SELECT description FROM unit_type WHERE id = t2_sighting.unit_type_id), "N/A") AS UnitType,
            t2_sighting.comments AS SightingComments
        FROM t2_survey
        LEFT JOIN t2_sighting ON t2_sighting.survey_id = t2_survey.id
        JOIN taxon ON t2_sighting.taxon_id = taxon.id
        JOIN source ON t2_survey.source_id = source.id
        JOIN t2_site ON t2_survey.site_id = t2_site.id
        WHERE source.id = {source_id}
    """

    db.sql("CREATE OR REPLACE TABLE t AS SELECT nextval('serial') AS id, ST_Point(X, Y) as Coords, * FROM mysql_query('mysqldb', '%s')" % sql1.replace("'", "''"))

    (c,) = db.sql("SELECT COUNT(*) FROM t").fetchone()

    db.sql("INSERT INTO t SELECT nextval('serial') AS id, ST_Point(X, Y) as Coords, * FROM mysql_query('mysqldb', '%s')" % sql2.replace("'", "''"))
    db.sql("""CREATE INDEX coord_idx ON t USING RTREE (Coords)""")
    db.sql("""CREATE OR REPLACE TABLE t_region AS
        SELECT t.id, MIN(region.id) AS region_id
        FROM t
        JOIN region ON ST_Contains(region.geom, t.Coords)
        GROUP BY t.id
        """)

    db.sql("""CREATE OR REPLACE TABLE t AS
        SELECT t.*,
            region.name AS Region,
            region.state AS State,
            region.lon AS RegionCentroidLongitude,
            region.lat AS RegionCentroidLatitude
        FROM t
        LEFT JOIN t_region ON t.id = t_region.id
        LEFT JOIN region ON t_region.region_id = region.id""")

    # t1 aggregation
    db.sql("""
        CREATE OR REPLACE TABLE month_agg AS
        SELECT
            SUBSTR(TRIM('_' FROM REGEXP_REPLACE(ScientificName, '[^a-zA-Z]', '_', 'g')), 1, 40) AS Binomial,
            TimeSeriesID,
            DataType,
            StartYear,
            StartMonth,
            SourceID,
            SourceDesc,
            DataProcessingType,
            TaxonID,
            CommonName,
            "Order",
            ScientificName,
            Family,
            FamilyCommonName,
            Class,
            EligibleForTSX,
            TaxonomicGroup,
            EPBCStatus,
            IUCNStatus,
            BirdActionPlanStatus,
            MaxStatus,
            SiteID,
            SiteName,
            State,
            Region,
            RegionCentroidLongitude,
            RegionCentroidLatitude,
            AVG(X) AS SurveysCentroidLongitude,
            AVG(Y) AS SurveysCentroidLatitude,
            MAX(PositionalAccuracyInM) AS SurveysSpatialAccuracyInMetres,
            SearchTypeDesc,
            UnitOfMeasurement,
            MonitoringProgram,
            Management,
            ManagementCategory,
            COUNT(DISTINCT SurveyID) AS SurveyCount,
            AVG(Count) AS Val
        FROM t
        WHERE DataType = 1
        GROUP BY ALL;

        CREATE OR REPLACE TABLE year_agg AS
        SELECT * EXCLUDE (Val, SurveyCount, StartMonth, SurveysCentroidLongitude, SurveysCentroidLatitude, SurveysSpatialAccuracyInMetres),
            AVG(SurveysCentroidLongitude) AS SurveysCentroidLongitude,
            AVG(SurveysCentroidLatitude) AS SurveysCentroidLatitude,
            MAX(SurveysSpatialAccuracyInMetres) AS SurveysSpatialAccuracyInMetres,
            AVG(Val) AS Val,
            SUM(SurveyCount) AS SurveyCount
        FROM month_agg
        GROUP BY ALL;
    """)

    output_path = os.path.join(data_dir('preprocessed'), "%s_raw.parquet" % source_id)
    db.sql("COPY t TO '%s'" % output_path)

    output_path = os.path.join(data_dir('preprocessed'), "%s_agg_t1.parquet" % source_id)
    db.sql("COPY year_agg TO '%s'" % output_path)


if __name__ == '__main__':
    main()

import duckdb
from tsx.db.connect import get_database_duckdb_attach_string, get_session, get_mysql_connection
from tsx.config import data_dir
import os
from tqdm import tqdm
from sqlalchemy import text
import pandas as pd
import tempfile
from tsx.util import delete_file_if_exists
from threading import Lock

from mysql.connector import FieldType
import pyarrow as pa
import pyarrow.parquet

preprocessed_data_dir = data_dir('preprocessed')

def raw_data_glob():
    return os.path.join(preprocessed_data_dir, '*_raw.parquet').replace("'", "''")

def aggregated_data_glob():
    return os.path.join(preprocessed_data_dir, '*_agg*.parquet').replace("'", "''")

def aggregated_data_path(source_id, data_type):
    return os.path.join(preprocessed_data_dir, '%s_agg_t%s.parquet' % (source_id, data_type))

def raw_data_path(source_id):
    return os.path.join(preprocessed_data_dir, '%s_raw.parquet' % (source_id,))


def main():
    session = get_session()
    session.connection(execution_options = { 'stream_results': True})
    source_ids = [x for (x,) in session.execute(text("SELECT id FROM source")).fetchall()]

    with get_mysql_connection() as conn:
        preprocess_sources(source_ids, conn)

def arrow_type_from_mysql_column_description(description):
    # https://peps.python.org/pep-0249/#description
    (name, type_code, display_size, internal_size, precision, scale, null_ok) = description[0:7]

    if type_code == FieldType.DECIMAL or type_code == FieldType.NEWDECIMAL:
        if precision <= 38:
            return pa.decimal128(precision, scale)
        elif precision <= 76:
            return pa.decimal256(precision, scale)
        else:
            return ValueError("Cannot represent decimal with precision greater than 76")
    elif type_code == FieldType.TINY:
        return pa.int8()
    elif type_code == FieldType.SHORT:
        return pa.int16()
    elif type_code == FieldType.LONG:
        return pa.int32()
    elif type_code == FieldType.FLOAT:
        return pa.float32()
    elif type_code == FieldType.DOUBLE:
        return pa.float64()
    elif type_code == FieldType.NULL:
        return pa.null()
    elif type_code == FieldType.TIMESTAMP:
        return pa.timestamp('us')
    elif type_code == FieldType.LONGLONG:
        return pa.int64()
    elif type_code == FieldType.INT24:
        return pa.int32()
    elif type_code == FieldType.DATE:
        return pa.date64()
    elif type_code == FieldType.TIME:
        return pa.time64('us')
    elif type_code == FieldType.DATETIME:
        return pa.timestamp('us')
    elif type_code == FieldType.YEAR:
        return pa.int8()
    elif type_code == FieldType.NEWDATE:
        return pa.date64()
    elif type_code == FieldType.VARCHAR:
        return pa.string()
    elif type_code == FieldType.BIT:
        return pa.bool_()
    elif type_code == FieldType.VECTOR:
        raise ValueError("Unsupported data type VECTOR")
    elif type_code == FieldType.JSON:
        return pa.json_()
    elif type_code == FieldType.ENUM:
        raise ValueError("Unsupported data type ENUM")
    elif type_code == FieldType.SET:
        raise ValueError("Unsupported data type SET")
    elif type_code == FieldType.TINY_BLOB:
        return pa.binary()
    elif type_code == FieldType.MEDIUM_BLOB:
        return pa.binary()
    elif type_code == FieldType.LONG_BLOB:
        return pa.binary()
    elif type_code == FieldType.BLOB:
        return pa.binary()
    elif type_code == FieldType.VAR_STRING:
        return pa.string()
    elif type_code == FieldType.STRING:
        return pa.string()
    elif type_code == FieldType.GEOMETRY:
        raise ValueError("Unsupported data type GEOMETRY")

    raise value_error("Unrecognized type_code: %s" % type_code)


def mysql_to_parquet(conn, path_pattern, sql, chunksize=65536):
    result = []
    cur = conn.cursor(buffered=False, raw=False)
    cur.arraysize = chunksize
    cur.execute(sql)

    names = [col[0] for col in cur.description]
    types = [arrow_type_from_mysql_column_description(x) for x in cur.description]

    index = 0
    while True:
        rows = cur.fetchmany(chunksize)
        if len(rows):
            data = [
                pa.array([row[index] for row in rows], type = type)
                for (index, type)
                in enumerate(types)
            ]
            table = pa.Table.from_arrays(data, names)
            path = path_pattern % index
            pyarrow.parquet.write_table(table, path)
            result.append(path)
            index += 1
            print(path)
        else:
            break

    return result


def remove_preprocessed_data(source_id):
    for filename in [
        "%s_raw.parquet" % source_id,
        "%s_agg_t1.parquet" % source_id,
        "%s_agg_t2.parquet" % source_id,
    ]:
        path = os.path.join(data_dir('preprocessed'), filename)
        delete_file_if_exists(path)


def preprocess_sources(source_ids, conn):
    with tempfile.TemporaryDirectory(prefix="tsx") as tempdir:
        db = duckdb.connect()
        db.sql("INSTALL spatial")
        db.sql("LOAD spatial")
        db.sql("CREATE SEQUENCE serial")

        attach_region_db(db)

        for source_id in tqdm(source_ids):
            preprocess_source(source_id, db, conn, tempdir)

def preprocess_source(source_id, db, conn, tempdir):
    sql1 = f"""
        SELECT
            CONCAT(source.id, '_', t1_sighting.unit_id, '_', COALESCE(t1_site.search_type_id, '0'), '_', t1_site.id, '_', taxon.id) AS TimeSeriesID,
            t1_survey.id AS SurveyID,
            t1_sighting.id AS SightingID,
            t1_survey.data_import_id AS DataImportID,
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
            t2_survey.data_import_id AS DataImportID,
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

    db.sql("DROP TABLE IF EXISTS t")

    parquet_files = []

    path_pattern = os.path.join(tempdir, "raw_t1_%09d.parquet")
    parquet_files.extend(mysql_to_parquet(conn, path_pattern, sql1))

    path_pattern = os.path.join(tempdir, "raw_t2_%09d.parquet")
    parquet_files.extend(mysql_to_parquet(conn, path_pattern, sql2))

    if parquet_files:
        with db.cursor() as cursor:
            # These type casts are to ensure that types are consistent accross all files
            cursor.execute("""
                CREATE TABLE t AS SELECT
                    nextval('serial') AS id,
                    ST_Point(X, Y) as Coords,
                    TimeSeriesID::VARCHAR AS TimeSeriesID,
                    SurveyID::INTEGER AS SurveyID,
                    SightingID::INTEGER AS SightingID,
                    DataType::INTEGER AS DataType,
                    SourceType::VARCHAR AS SourceType,
                    EligibleForTSX::BOOLEAN AS EligibleForTSX,
                    TaxonomicGroup::VARCHAR AS TaxonomicGroup,
                    EPBCStatus::VARCHAR AS EPBCStatus,
                    IUCNStatus::VARCHAR AS IUCNStatus,
                    BirdActionPlanStatus::VARCHAR AS BirdActionPlanStatus,
                    MaxStatus::VARCHAR AS MaxStatus,
                    SourceID::INTEGER AS SourceID,
                    DataImportID::INTEGER AS DataImportID,
                    SourceDesc::VARCHAR AS SourceDesc,
                    SourceProvider::VARCHAR AS SourceProvider,
                    DataProcessingType::VARCHAR AS DataProcessingType,
                    LocationName::VARCHAR AS LocationName,
                    SearchTypeDesc::VARCHAR AS SearchTypeDesc,
                    SourcePrimaryKey::VARCHAR AS SourcePrimaryKey,
                    StartMonth::INTEGER AS StartMonth,
                    StartYear::INTEGER AS StartYear,
                    StartDate::VARCHAR AS StartDate,
                    FinishDate::VARCHAR AS FinishDate,
                    StartTime::VARCHAR AS StartTime,
                    FinishTime::VARCHAR AS FinishTime,
                    DurationInMinutes::VARCHAR AS DurationInMinutes,
                    "DurationInDays/Nights"::VARCHAR AS "DurationInDays/Nights",
                    "NumberOfTrapsPerDay/Night"::VARCHAR AS "NumberOfTrapsPerDay/Night",
                    AreaInM2::DOUBLE AS AreaInM2,
                    LengthInKm::DOUBLE AS LengthInKm,
                    SiteID::INTEGER AS SiteID,
                    SiteName::VARCHAR AS SiteName,
                    Y::DOUBLE AS Y,
                    X::DOUBLE AS X,
                    ProjectionReference::VARCHAR AS ProjectionReference,
                    PositionalAccuracyInM::DOUBLE AS PositionalAccuracyInM,
                    SurveyComments::VARCHAR AS SurveyComments,
                    MonitoringProgram::VARCHAR AS MonitoringProgram,
                    MonitoringProgramComments::VARCHAR AS MonitoringProgramComments,
                    Management::VARCHAR AS Management,
                    ManagementCategory::VARCHAR AS ManagementCategory,
                    ManagementCategoryComments::VARCHAR AS ManagementCategoryComments,
                    TaxonID::VARCHAR AS TaxonID,
                    CommonName::VARCHAR AS CommonName,
                    "Order"::VARCHAR AS "Order",
                    ScientificName::VARCHAR AS ScientificName,
                    Family::VARCHAR AS Family,
                    FamilyCommonName::VARCHAR AS FamilyCommonName,
                    Class::VARCHAR AS Class,
                    Count::DOUBLE AS Count,
                    UnitOfMeasurement::VARCHAR AS UnitOfMeasurement,
                    UnitType::VARCHAR AS UnitType,
                    SightingComments::VARCHAR AS SightingComments
                FROM read_parquet($files)""",
                {"files": parquet_files})
    else:
        return "Skipping empty source: %s" % source_id

    # db.sql("CREATE OR REPLACE TABLE t AS SELECT nextval('serial') AS id, ST_Point(X, Y) as Coords, * FROM mysql_query('mysqldb', '%s')" % sql1.replace("'", "''"))
    # db.sql("INSERT INTO t SELECT nextval('serial') AS id, ST_Point(X, Y) as Coords, * FROM mysql_query('mysqldb', '%s')" % sql2.replace("'", "''"))

    db.sql("""CREATE INDEX coord_idx ON t USING RTREE (Coords)""")
    db.sql("""CREATE OR REPLACE TABLE t_region AS
        SELECT t.id, MIN(region.id) AS region_id
        FROM t
        JOIN region.region ON ST_Contains(region.geom, t.Coords)
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
        LEFT JOIN region.region ON t_region.region_id = region.id""")

    # t1 aggregation
    db.sql("""
        CREATE OR REPLACE TABLE month_agg AS
        SELECT
            SUBSTR(TRIM('_' FROM REGEXP_REPLACE(ScientificName, '[^a-zA-Z]', '_', 'g')), 1, 40) AS Binomial,
            TimeSeriesID,
            DataImportID,
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

    output_path = raw_data_path(source_id)
    db.sql("COPY t TO '%s'" % output_path)

    output_path = aggregated_data_path(source_id, 1)
    db.sql("COPY year_agg TO '%s'" % output_path)


def attach_region_db(db):
    ensure_region_db_exists()
    db.sql("ATTACH '%s' AS region (READ_ONLY)" % region_db_path())


def region_db_path():
    return os.path.join(data_dir('cache'), "region.duckdb")

region_db_lock = Lock()
def ensure_region_db_exists():
    with region_db_lock:
        path = region_db_path()
        if os.path.exists(path):
            print("Existing region DB found")
            return
        print("Creating region DB")

        db = duckdb.connect(path)
        db.sql("LOAD mysql")
        db.sql("INSTALL spatial")
        db.sql("LOAD spatial")
        db.sql("ATTACH '%s' AS mysqldb (TYPE mysql)" % get_database_duckdb_attach_string())

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
        db.close()

if __name__ == '__main__':
    main()

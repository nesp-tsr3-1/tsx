from flask import Blueprint, jsonify, request, send_file, session, Response
import csv
from uuid import uuid4
from tsx.api.util import db_session, get_user, get_roles
from tsx.api.permissions import permitted
from tsx.config import data_dir
import os
from threading import Thread, Lock
import shutil
import subprocess
import importlib.resources

bp = Blueprint('subset', __name__)

class EchoWriter:
    def write(self, line):
        return line

def stream_csv(result):
    writer = csv.writer(EchoWriter())
    yield writer.writerow(result.keys())
    for row in result.fetchall():
        yield writer.writerow(row)

def save_csv(result, file):
    with open(file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(result.keys())
        for row in result.fetchall():
            writer.writerow(row)

@bp.route('/subset/raw_data', methods = ['GET'])
def subset_raw_data():
    result = query_subset_raw_data()
    response = Response(stream_csv(result), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=raw_data.csv'
    return response

@bp.route('/subset/stats', methods = ['GET'])
def subset_stats():
    where_conditions, having_conditions, params = subset_sql_params()

    sql = """WITH t AS (SELECT
            t1_survey.id AS survey_id,
            t1_sighting.id AS sighting_id,
            t1_sighting.taxon_id,
            MIN(region.state) AS State,
            t1_sighting.unit_id,
            t1_survey.site_id,
            t1_survey.source_id,
            t1_site.search_type_id
        FROM t1_survey STRAIGHT_JOIN region_subdiv
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        STRAIGHT_JOIN region ON region.id = region_subdiv.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        LEFT JOIN intensive_management ON t1_site.intensive_management_id = intensive_management.id
        WHERE ST_Contains(region_subdiv.geometry, coords)
        AND {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause})
        SELECT
            COUNT(DISTINCT survey_id) AS survey_count,
            COUNT(DISTINCT sighting_id) AS sighting_count,
            COUNT(DISTINCT taxon_id) AS taxon_count,
            COUNT(DISTINCT source_id) AS source_count,
            COUNT(DISTINCT site_id, taxon_id, source_id, unit_id, search_type_id) AS time_series_count
        FROM t
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    result = db_session.execute(sql, params).fetchone()
    return jsonify(dict(result))

def subset_sql_params():
    where_conditions = []
    having_conditions = []
    params = {}

    args = request.get_json() or request.args

    print(args)

    if 'state' in args:
        having_conditions.append("State = :state")
        params['state'] = args['state']

    if 'monitoring_programs' in args:
        ids = args['monitoring_programs']
        if isinstance(ids, str):
            ids = ids.split(",")
        pnames = ["mp%s" % i for i in range(0, len(ids))]

        where_conditions.append("source.monitoring_program_id IN (%s)" % ", ".join([":%s" % p for p in pnames]))
        params.update(dict(zip(pnames, ids)))

    if 'intensive_management' in args:
        management = args['intensive_management']
        if management == "Any management":
            where_conditions.append("COALESCE(intensive_management.`grouping`, 'No known management') != 'No known management'")
        elif management == "Predator-free":
            where_conditions.append("intensive_management.`grouping` LIKE '%predator-free%'")
        elif management == "Translocation":
            where_conditions.append("intensive_management.`grouping` LIKE '%translocation%'")
        elif management == "No known management":
            where_conditions.append("COALESCE(intensive_management.`grouping`, 'No known management') = 'No known management'")

    if 'taxon_id' in args:
        where_conditions.append('taxon.id = :taxon_id')
        params['taxon_id'] = args['taxon_id']

    if 'source_id' in args:
        where_conditions.append('source.id = :source_id')
        params['source_id'] = args['source_id']

    return (where_conditions, having_conditions, params)

def query_subset_raw_data_sql_and_params():
    where_conditions, having_conditions, params = subset_sql_params()

    params['redact_location'] = ('source_id' not in params) or not permitted(get_user(), 'import_data', 'source', params['source_id'])

    sql = """
        SELECT
            (SELECT description FROM source_type WHERE id = source.source_type_id) AS SourceType,
            source.description AS SourceDesc,
            source.provider AS SourceProvider,
            t1_survey.location AS LocationName,
            (SELECT description FROM search_type WHERE id = t1_site.search_type_id) AS SearchTypeDesc,
            t1_survey.source_primary_key AS SourcePrimaryKey,
            CONCAT(
                COALESCE(CONCAT(LPAD(start_date_d, 2, 0), '/'), ''),
                COALESCE(CONCAT(LPAD(start_date_m, 2, 0), '/'), ''),
                start_date_y
            ) AS StartDate,
            CONCAT(
                COALESCE(CONCAT(LPAD(finish_date_d, 2, 0), '/'), ''),
                COALESCE(CONCAT(LPAD(finish_date_m, 2, 0), '/'), ''),
                finish_date_y
            ) AS FinishDate,
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
            t1_site.name AS SiteName,
            IF(:redact_location, 'REDACTED', ST_Y(t1_survey.coords)) as Y,
            IF(:redact_location, 'REDACTED', ST_X(t1_survey.coords)) as X,
            'GDA94' AS ProjectionReference,
            t1_survey.positional_accuracy_in_m AS PositionalAccuracyInM,
            t1_survey.comments AS SurveyComments,
            (SELECT description FROM monitoring_program WHERE id = source.monitoring_program_id) AS MonitoringProgram,
            t1_sighting.taxon_id AS TaxonID,
            taxon.common_name AS CommonName,
            taxon.scientific_name AS ScientificName,
            t1_sighting.`count` AS Count,
            (SELECT description FROM unit WHERE id = t1_sighting.unit_id) AS UnitOfMeasurement,
            MIN(region.state) AS State,
            MIN(region.name) AS Region,
            CASE WHEN intensive_management_id IS NULL THEN NULL ELSE COALESCE(intensive_management.`grouping`, 'Other') END AS intensive_management_grouping
        FROM t1_survey STRAIGHT_JOIN region_subdiv
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        JOIN region ON region.id = region_subdiv.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        LEFT JOIN intensive_management ON t1_site.intensive_management_id = intensive_management.id
        WHERE ST_Contains(region_subdiv.geometry, coords)
        AND {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause}
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    return sql, params

def query_subset_raw_data():
    sql, params = query_subset_raw_data_sql_and_params()
    return db_session.execute(sql, params)


@bp.route('/subset/time_series', methods = ['GET'])
def subset_time_series():
    result = query_subset_time_series()
    response = Response(stream_csv(result), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=time_series.csv'
    return response

def query_subset_time_series():
    where_conditions, having_conditions, params = subset_sql_params()

# Note STRAIGHT_JOINs are just trial and error to get a decent query plan
# I actually want to a LEFT JOIN between survey and region but I can't figure out how to get usable performance.
    raw_data_sql = """
        SELECT
            t1_survey.id AS survey_id,
            t1_survey.site_id,
            t1_sighting.taxon_id,
            t1_survey.source_id,
            t1_sighting.unit_id,
            t1_site.search_type_id,
            t1_survey.start_date_y,
            t1_survey.start_date_m,
            MIN(region.state) AS State,
            MIN(region.name) AS Region,
            t1_sighting.`count` AS x
        FROM t1_survey STRAIGHT_JOIN region_subdiv
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        STRAIGHT_JOIN region ON region.id = region_subdiv.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        LEFT JOIN intensive_management ON t1_site.intensive_management_id = intensive_management.id
        WHERE ST_Contains(region_subdiv.geometry, coords)
        AND {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause}
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    sql = """WITH t AS (%s)
        SELECT
            MIN(start_date_y) AS min_year,
            MAX(start_date_y) AS max_year
        FROM t""" % raw_data_sql

    (min_year, max_year) = db_session.execute(sql, params).fetchone()



    year_fields_sql = ",\n".join(
        "AVG(IF(start_date_y = %s, x, NULL)) AS `%s`" % (year, year) for year in range(min_year, max_year + 1))

    sql = """WITH t AS (%s),
        t2 AS (SELECT
            t.site_id,
            t.taxon_id,
            t.source_id,
            t.unit_id,
            t.search_type_id,
            t.start_date_y,
            t.start_date_m,
            t.State,
            t.Region,
            AVG(ST_Y(t1_survey.coords)) AS surveys_centroid_lat,
            AVG(ST_X(t1_survey.coords)) AS surveys_centroid_lon,
            COUNT(DISTINCT t.survey_id) AS survey_count,
            MAX(t1_survey.positional_accuracy_in_m) AS positional_accuracy_in_m,
            AVG(t.x) AS x
        FROM t
        JOIN t1_survey ON t1_survey.id = t.survey_id
        GROUP BY
            site_id,
            taxon_id,
            source_id,
            unit_id,
            search_type_id,
            start_date_y,
            start_date_m,
            State, Region
        )
        SELECT
            SUBSTR(TRIM('_' FROM REGEXP_REPLACE(taxon.scientific_name, '[^a-zA-Z]', '_')), 1, 40) AS Binomial,
            ROW_NUMBER() OVER () AS ID,
            CONCAT(t2.source_id, '_', t2.unit_id, '_', COALESCE(t2.search_type_id, '0'), '_', t2.site_id, '_', t2.taxon_id) AS TimeSeriesID,
            taxon.id AS TaxonID,
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
            (SELECT description FROM search_type WHERE id = t2.search_type_id) AS SearchTypeDesc,
            t2.site_id AS SiteID,
            t1_site.name AS SiteDesc,
            (SELECT description FROM intensive_management WHERE t1_site.intensive_management_id = intensive_management.id) AS IntensiveManagement,
            source.id AS SourceID,
            source.description AS SourceDesc,
            (SELECT description FROM monitoring_program WHERE source.monitoring_program_id = monitoring_program.id) AS MonitoringProgram,
            (SELECT description FROM unit WHERE id = t2.unit_id) AS Unit,
            t2.State,
            t2.Region,
            ROUND(t2.surveys_centroid_lat, 7) AS SurveysCentroidLatitude,
            ROUND(t2.surveys_centroid_lon, 7) AS SurveysCentroidLongitude,
            SUM(t2.survey_count) AS SurveyCount,
            MAX(t2.positional_accuracy_in_m) AS SurveysSpatialAccuracyInMetres,
            %s,
            MAX(start_date_y) - MIN(start_date_y) + 1 AS TimeSeriesLength,
            COUNT(DISTINCT start_date_y) AS TimeSeriesSampleYears,
            COUNT(DISTINCT start_date_y) / (MAX(start_date_y) - MIN(start_date_y) + 1) AS TimeSeriesCompleteness
        FROM t2
        JOIN taxon ON taxon.id = t2.taxon_id
        JOIN t1_site ON t1_site.id = t2.site_id
        JOIN source ON source.id = t2.source_id
        GROUP BY
            t2.site_id,
            t2.taxon_id,
            t2.source_id,
            t2.unit_id,
            t2.search_type_id,
            State, Region, surveys_centroid_lat, surveys_centroid_lon
        """ % (raw_data_sql, year_fields_sql)

    return db_session.execute(sql, params)


def trend_work_dir(trend_id):
    return os.path.join(data_dir("processed_data"), "subset", trend_id)


lock = Lock()
processing_trend_ids = set()

def process_trend(trend_id):
    with lock:
        processing_trend_ids.add(trend_id)
    try:
        path = trend_work_dir(trend_id)
        subprocess.run(["Rscript", os.path.join(path, "lpi.R"), os.path.join(path, "lpi.csv"), path])
        shutil.copy(os.path.join(path, "data_infile_Results.txt"), os.path.join(path, "trend.txt"))
    finally:
        with lock:
            processing_trend_ids.remove(trend_id)

@bp.route('/subset/trend', methods = ['POST'])
def subset_generate_trend():
    trend_id = str(uuid4())

    path = trend_work_dir(trend_id)
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "lpi.R"), "wb") as f:
        f.write(importlib.resources.read_binary("tsx.resources", "lpi.R"))

    result = query_subset_time_series()
    save_csv(result, os.path.join(path, "lpi.csv"))

    t = Thread(target = process_trend, args = (trend_id,))
    t.start()

    return jsonify({"id": trend_id}), 201

@bp.route('/subset/trend/<trend_id>/status')
def subset_get_trend_status(trend_id):
    path = os.path.join(trend_work_dir(trend_id), "trend.txt")
    if os.path.exists(path):
        return jsonify({"status": "ready"})
    else:
        with lock:
            if trend_id in processing_trend_ids:
                return jsonify({"status": "processing"})
            else:
                return "Not found", 404


@bp.route('/subset/trend/<trend_id>')
def subset_get_trend(trend_id):
    path = os.path.join(trend_work_dir(trend_id), "trend.txt")
    if os.path.exists(path):
        return send_file(path, mimetype = 'text/plain', cache_timeout = 5, as_attachment=True, attachment_filename='trend.txt')
    else:
        return "Not found", 404

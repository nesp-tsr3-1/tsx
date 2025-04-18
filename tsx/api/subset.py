from flask import Blueprint, jsonify, request, send_file, session, Response
import csv
from uuid import uuid4
from tsx.api.util import db_session, get_user, get_roles, jsonify_rows, get_request_args_or_body, sanitise_file_name_string
from tsx.api.permissions import permitted
from tsx.api.results import trend_txt_to_csv
from tsx.config import data_dir
import os
from threading import Thread, Lock
import shutil
import subprocess
import importlib.resources
import io
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
import json
from sqlalchemy import text
import hashlib

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
        write_csv(result, f)

def csv_string(result):
    with io.StringIO() as out:
        write_csv(result, out)
        return out.getvalue()

def write_csv(result, output):
    writer = csv.writer(output)
    writer.writerow(result.keys())
    for row in result.fetchall():
        writer.writerow(row)


@bp.route('/subset/raw_data', methods = ['GET'])
def subset_raw_data():
    if not params_permitted():
        return "Not authorised", 401

    zip_filename = 'tsx-raw-data.zip'
    csv_filename = 'raw-data&%s.csv' % filename_component_from_params()

    result = query_subset_raw_data()
    extra_dir = data_dir('raw-download-extras')
    extra_entries = [(filename, os.path.join(extra_dir, filename), 'file') for filename in os.listdir(extra_dir)]
    return zip_response([(csv_filename, csv_string(result), 'str')] + extra_entries, zip_filename)

@bp.route('/subset/stats', methods = ['GET'])
def subset_stats():
    where_conditions, having_conditions, params = subset_sql_params()

    sql = """WITH t AS (SELECT
            t1_survey.id AS survey_id,
            t1_sighting.id AS sighting_id,
            t1_sighting.taxon_id,
            region.state AS State,
            t1_sighting.unit_id,
            t1_survey.site_id,
            t1_survey.source_id,
            t1_site.search_type_id,
            MIN(t1_survey.start_date_y) AS min_year,
            MAX(t1_survey.start_date_y) AS max_year
        FROM t1_survey
        LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
        LEFT JOIN region ON region.id = t1_survey_region.region_id
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        WHERE {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause})
        SELECT
            COUNT(DISTINCT survey_id) AS survey_count,
            COUNT(DISTINCT sighting_id) AS sighting_count,
            COUNT(DISTINCT taxon_id) AS taxon_count,
            COUNT(DISTINCT source_id) AS source_count,
            COUNT(DISTINCT site_id, taxon_id, source_id, unit_id, search_type_id) AS time_series_count,
            MIN(min_year) AS min_year,
            MAX(max_year) AS max_year
        FROM t
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    result = db_session.execute(text(sql), params).fetchone()
    return jsonify(dict(result._mapping))

@bp.route('/subset/intensity_map', methods = ['GET'])
def subset_intensity_map():
    return jsonify(subset_intensity_map_json()), 200

def subset_intensity_map_json(subset_params=None):
    where_conditions, having_conditions, params = subset_sql_params(subset_params)

    sql = """WITH t AS (SELECT
            t1_survey.id AS survey_id,
            t1_survey.coords AS coords,
            t1_sighting.id AS sighting_id,
            t1_sighting.taxon_id,
            region.state AS State,
            t1_sighting.unit_id,
            t1_survey.site_id,
            t1_survey.source_id,
            t1_site.search_type_id
        FROM t1_survey
        LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
        LEFT JOIN region ON region.id = t1_survey_region.region_id
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        WHERE {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause})
        SELECT
            ROUND(ST_X(coords), 1) AS lon,
            ROUND(ST_Y(coords), 1) AS lat,
            COUNT(DISTINCT site_id, taxon_id, source_id, unit_id, search_type_id) AS c
        FROM t
        GROUP BY lat, lon
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    result = db_session.execute(text(sql), params).fetchall()
    return [dict(row._mapping) for row in result]

@bp.route('/subset/sites', methods = ['GET'])
def subset_sites():
    where_conditions, having_conditions, params = subset_sql_params(state_via_region=True)

    order_by_expressions = []

    if request.args.get('site_name_query'):
        params['site_name_query'] = request.args['site_name_query'].strip()
        params['site_name_query_pattern'] = '%' + request.args['site_name_query'].strip() + '%'

        where_conditions.append("t1_site.name LIKE :site_name_query_pattern")
        order_by_expressions.append("INSTR(t1_site.name, :site_name_query)")

    order_by_expressions.append("t1_site.name")

    sql = """SELECT DISTINCT t1_site.id, t1_site.name
        FROM t1_survey
        LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
        LEFT JOIN region ON region.id = t1_survey_region.region_id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        WHERE {where_clause}
        ORDER BY {order_by_clause}
        LIMIT 300
    """.format(where_clause=" AND ".join(where_conditions) or "TRUE",
        order_by_clause=", ".join(order_by_expressions))

    result = db_session.execute(text(sql), params).fetchall()
    return jsonify_rows(result)

@bp.route('/subset/species', methods = ['GET'])
def subset_species():
    where_conditions, having_conditions, params = subset_sql_params(state_via_region=True)
    order_by_expressions = []

    if request.args.get('species_name_query'):
        params['species_name_query'] = request.args['species_name_query'].strip()
        params['species_name_query_pattern'] = '%' + request.args['species_name_query'].strip() + '%'

        where_conditions.append("""
            (
                COALESCE(taxon.common_name, "") LIKE :species_name_query_pattern OR
                COALESCE(taxon.scientific_name, "") LIKE :species_name_query_pattern OR
                COALESCE(taxon.id, "") LIKE :species_name_query_pattern
            )
        """)
        order_by_expressions.append("""
            LEAST(
                IF(INSTR(COALESCE(taxon.common_name, ""), :species_name_query), INSTR(COALESCE(taxon.common_name, ""), :species_name_query), 100000),
                IF(INSTR(COALESCE(taxon.scientific_name, ""), :species_name_query), INSTR(COALESCE(taxon.scientific_name, ""), :species_name_query), 100000),
                IF(INSTR(COALESCE(taxon.id, ""), :species_name_query), INSTR(COALESCE(taxon.id, ""), :species_name_query), 100000)
            )
        """)

    order_by_expressions.append("taxon.scientific_name")

    sql = """SELECT DISTINCT taxon.id, taxon.common_name, taxon.scientific_name
            FROM t1_survey
            LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
            LEFT JOIN region ON region.id = t1_survey_region.region_id
            JOIN t1_site ON t1_survey.site_id = t1_site.id
            JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
            JOIN taxon ON t1_sighting.taxon_id = taxon.id
            JOIN source ON t1_survey.source_id = source.id
            WHERE {where_clause}
        ORDER BY {order_by_clause}
        LIMIT 300
    """.format(where_clause=" AND ".join(where_conditions) or "TRUE",
        order_by_clause=", ".join(order_by_expressions))

    result = db_session.execute(text(sql), params).fetchall()
    return jsonify_rows(result)


# This tries to strike a balance between a descriptive name and not being too long
def filename_component_from_params(params=None):
    if params == None:
        params = get_request_args_or_body()
    parts = []

    if 'source_id' in params:
        source_id = params['source_id']
        source_name = db_query_single("SELECT description FROM source WHERE id = :id", { 'id': source_id })
        parts.append(('dataset', "%s_%s" % (source_id, source_name)))

    if 'taxon_id' in params:
        taxon_list = params['taxon_id'].split(',')
        if len(taxon_list) > 1:
            parts.append(('taxon', ",".join(taxon_list)))
        else:
            taxon_id = taxon_list[0]
            sci_name = db_query_single("SELECT scientific_name FROM taxon WHERE id = :id", { 'id': taxon_id })
            parts.append(('taxon', '%s_%s' % (taxon_id, sci_name)))

    if 'state' in params:
        parts.append(('state', params['state']))

    if 'monitoring_programs' in params:
        ids = params['monitoring_programs']

        if isinstance(ids, str):
            ids = ids.split(",")

        if 'any' in ids:
            if 'none' in ids:
                pass
            else:
                parts.append(('monitoring_programs', 'any'))
        else:
            if -1 in ids:
                ids.remove(-1)
                ids.append('none')

            if len(ids) == 1 and ids[0] != 'none':
                monitoring_program_name = db_query_single("SELECT description FROM monitoring_program WHERE id = :id", { 'id': ids[0] })
                parts.append(('monitoring_programs', '%s_%s' % (ids[0], monitoring_program_name)))
            else:
                parts.append(('monitoring_programs', ",".join(ids)))

    if 'management' in params:
        parts.append(('management', params['management']))

    if 'taxonomic_group' in params:
        parts.append(('taxonomic_group', params['taxonomic_group']))

    if 'site_id' in params:
        parts.append(('site', params['site_id']))

    if 'reference_year' in params:
        parts.append(('reference_year', params['reference_year']))

    if 'final_year' in params:
        parts.append(('final_year', params['final_year']))

    result = sanitise_file_name_string("&".join("%s=%s" % (k, v) for k, v in parts))

    # Truncate result if too long and add hash
    max_len = 128
    hash_len = 8
    if len(result) > max_len:
        h = hashlib.md5(result.encode('utf-8')).hexdigest()[0:hash_len]
        result = result[0:(max_len - hash_len - 1)] + "_" + h

    return result

def db_query_single(sql, params):
    result = db_session.execute(text(sql), params).fetchall()
    if len(result) == 1:
        return result[0][0]
    else:
        return None


def subset_sql_params(subset_params=None, state_via_region=False):
    where_conditions = []
    having_conditions = []
    params = {}

    args = subset_params or get_request_args_or_body()

    if 'state' in args:
        if state_via_region:
            where_conditions.append("region.state = :state")
            params['state'] = args['state']
        else:
            having_conditions.append("State = :state")
            params['state'] = args['state']

    if 'monitoring_programs' in args:
        ids = args['monitoring_programs']
        if isinstance(ids, str):
            ids = ids.split(",")

        if 'any' in ids:
            if 'none' in ids:
                pass
            else:
                where_conditions.append("source.monitoring_program_id IS NOT NULL")
        else:
            if 'none' in ids:
                ids.remove('none')
                ids.append(-1)

            pnames = ["mp%s" % i for i in range(0, len(ids))]
            where_conditions.append("COALESCE(source.monitoring_program_id, -1) IN (%s)" % ", ".join([":%s" % p for p in pnames]))
            params.update(dict(zip(pnames, ids)))

    if 'management' in args:
        management = args['management']
        where_conditions.append("t1_site.management_id IN (SELECT id FROM management WHERE type = :management)")
        params['management'] = management

    if 'taxon_id' in args:
        taxon_list = args['taxon_id'].split(',')
        param_names = ['taxon_id_%s' % i for i in range(0, len(taxon_list))]
        params.update(dict(zip(param_names, taxon_list)))
        where_conditions.append('taxon.id IN (%s)' % ",".join(":" + p for p in param_names))

    if 'taxonomic_group' in args:
        params.update({ 'taxonomic_group': args['taxonomic_group'] })
        where_conditions.append('taxon.taxonomic_group = :taxonomic_group')

    if 'status_auth' in args and 'taxon_status' in args:
        status_auth = args['status_auth']
        taxon_status = args['taxon_status'].split(',')
        if status_auth in ["max", "epbc", "iucn", "bird_action_plan"]:
            param_names = ['taxon_status_id_%s' % i for i in range(0, len(taxon_status))]
            params.update(dict(zip(param_names, taxon_status)))
            param_placeholder = ",".join(":" + p for p in param_names)
            where_conditions.append('COALESCE(%s_status_id, 1) IN (SELECT id FROM taxon_status WHERE code IN (%s))' % (status_auth, param_placeholder))

    if 'source_id' in args:
        where_conditions.append('source.id = :source_id')
        params['source_id'] = args['source_id']

    if 'site_id' in args:
        try:
            ids = args['site_id'].split(",")
            pnames = ["site%s" % i for i in range(0, len(ids))]
            where_conditions.append("t1_site.id IN (%s)" % ", ".join([":%s" % p for p in pnames]))
            params.update(dict(zip(pnames, ids)))
        except:
            pass

    return (where_conditions, having_conditions, params)

def query_subset_raw_data_sql_and_params():
    where_conditions, having_conditions, params = subset_sql_params()

    params['redact_location'] = not permitted(get_user(), 'import_data', 'source', params.get('source_id'))

    sql = """
        SELECT
            (SELECT description FROM source_type WHERE id = source.source_type_id) AS SourceType,
            source.description AS SourceDesc,
            source.provider AS SourceProvider,
            COALESCE((SELECT description FROM data_processing_type WHERE id = source.data_processing_type_id), "N/A") AS DataProcessingType,
            t1_survey.location AS LocationName,
            (SELECT description FROM search_type WHERE id = t1_site.search_type_id) AS SearchTypeDesc,
            t1_survey.source_primary_key AS SourcePrimaryKey,
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
            IF(:redact_location, 'REDACTED', t1_site.name) AS SiteName,
            IF(:redact_location, 'REDACTED', ST_Y(t1_survey.coords)) as Y,
            IF(:redact_location, 'REDACTED', ST_X(t1_survey.coords)) as X,
            'EPSG:4326' AS ProjectionReference,
            t1_survey.positional_accuracy_in_m AS PositionalAccuracyInM,
            region.state AS State,
            region.name AS Region,
            t1_survey.comments AS SurveyComments,
            (SELECT description FROM monitoring_program WHERE id = source.monitoring_program_id) AS MonitoringProgram,
            source.monitoring_program_comments AS MonitoringProgramComments,
            COALESCE((SELECT type FROM management WHERE id = t1_site.management_id), "No known management") AS Management,
            COALESCE((SELECT description FROM management WHERE id = t1_site.management_id), "Unknown") AS ManagementCategory,
            t1_site.management_comments AS ManagementCategoryComments,
            t1_sighting.taxon_id AS TaxonID,
            taxon.common_name AS CommonName,
            taxon.scientific_name AS ScientificName,
            t1_sighting.`count` AS Count,
            (SELECT description FROM unit WHERE id = t1_sighting.unit_id) AS UnitOfMeasurement,
            COALESCE((SELECT description FROM unit_type WHERE id = t1_sighting.unit_type_id), "N/A") AS UnitType,
            t1_sighting.comments AS SightingComments
        FROM t1_survey
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
        LEFT JOIN region ON region.id = t1_survey_region.region_id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        WHERE {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause}
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    return sql, params

def query_subset_raw_data():
    sql, params = query_subset_raw_data_sql_and_params()
    return db_session.execute(text(sql), params)


def params_permitted():
    if permitted(get_user(), '*', '*'):
        return True

    args = get_request_args_or_body()

    # Params must either be scoped to a source or a program that the user has access to download
    if 'source_id' in args:
        return permitted(get_user(), 'download_data', 'source', args['source_id'])

    if 'monitoring_programs' in args:
        ids = args['monitoring_programs']
        if isinstance(ids, str):
            ids = ids.split(",")
            for monitoring_program_id in ids:
                if not permitted(get_user(), 'download_data', 'program', monitoring_program_id):
                    return False
            if len(ids):
                return True

    return False

@bp.route('/subset/time_series', methods = ['GET'])
def subset_time_series():
    if not params_permitted():
        return "Not authorised", 401

    zip_filename = 'tsx-time-series.zip'
    csv_filename = 'time-series&%s.csv' % filename_component_from_params()

    result = query_subset_time_series()
    extra_dir = data_dir('time-series-download-extras')
    extra_entries = [(filename, os.path.join(extra_dir, filename), 'file') for filename in os.listdir(extra_dir)]
    return zip_response([(csv_filename, csv_string(result), 'str')] + extra_entries, zip_filename)


@bp.route('/subset/monitoring_consistency', methods = ['GET'])
def monitoring_consistency_plot():
    return jsonify(monitoring_consistency_plot_json()), 200

def monitoring_consistency_plot_json(subset_params=None):
    """Produces data for generating dot plots in the following format
    [
        [[year,count],[year,count] .. ],
        ...
    ]
    Where count = 0 or 1
    """
    result = query_subset_time_series(subset_params, random_sample_size=50)

    result_data = []

    numeric_keys = [(index, int(key)) for index, key in enumerate(result.keys()) if key.isdigit()]

    for row in result.fetchall():
        row_data = []
        for index, key in numeric_keys:
            value = row[index]
            if value != None:
                row_data.append([key, 1])
        result_data.append(row_data)

    return result_data


def stream_and_delete(filename):
    with open(filename, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            yield data
    os.remove(filename)

def stream_zip(entries):
    zip_filename = tempfile.mkstemp()[1]

    # Write zip file to temporary file
    with ZipFile(zip_filename, 'w', ZIP_DEFLATED) as zip_file:
        for name, data, datatype in entries:
            if datatype == 'str':
                zip_file.writestr(name, data)
            elif datatype == 'file':
                zip_file.write(data, name)

    return stream_and_delete(zip_filename)

def zip_response(entries, download_file_name):
    return Response(
        stream_zip(entries),
        mimetype="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=%s" % (download_file_name)
        }
    )

def query_subset_time_series(subset_params=None, random_sample_size=None):
    where_conditions, having_conditions, params = subset_sql_params(subset_params)

    if ('source_id' in params) and permitted(get_user(), 'import_data', 'source', params['source_id']):
        coordinates_sql = """
            AVG(t2.surveys_centroid_lat) AS SurveysCentroidLatitude,
            AVG(t2.surveys_centroid_lon) AS SurveysCentroidLongitude"""
    else:
        coordinates_sql = """
            ROUND(AVG(ST_Y(region.centroid)), 7) AS RegionCentroidLatitude,
            ROUND(AVG(ST_X(region.centroid)), 7) AS RegionCentroidLongitude"""

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
            region.id AS region_id,
            region.state AS State,
            t1_sighting.`count` AS x
        FROM t1_survey
        LEFT JOIN t1_survey_region ON t1_survey.id = t1_survey_region.survey_id
        LEFT JOIN region ON region.id = t1_survey_region.region_id
        JOIN t1_sighting ON t1_sighting.survey_id = t1_survey.id
        JOIN taxon ON t1_sighting.taxon_id = taxon.id
        JOIN source ON t1_survey.source_id = source.id
        JOIN t1_site ON t1_survey.site_id = t1_site.id
        WHERE {where_clause}
        GROUP BY t1_survey.id, t1_sighting.id
        {having_clause}
    """.format(
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE",
        having_clause = "HAVING " + " AND ".join(having_conditions) if having_conditions else "")

    sql = """WITH t AS (%s)
        SELECT DISTINCT start_date_y
        FROM t""" % raw_data_sql

    years = set(row[0] for row in db_session.execute(text(sql), params).fetchall())
    min_year = min(years)
    max_year = max(years)

    def year_field_sql(year, has_data):
        if has_data:
            return  "AVG(IF(start_date_y = %s, x, NULL)) AS `%s`" % (year, year)
        else:
            return "NULL as `%s`" % year

    year_fields_sql = ",\n".join(
        year_field_sql(year, year in years) for year in range(min_year, max_year + 1))

    if random_sample_size == None:
        random_sample_sql = ''
    else:
        random_sample_sql = 'ORDER BY MD5(TimeSeriesID) LIMIT %s' % int(random_sample_size)

    sql = """WITH t AS (%s),
        t2 AS (SELECT
            t.site_id,
            t.taxon_id,
            t.source_id,
            t.unit_id,
            t.search_type_id,
            t.start_date_y,
            t.start_date_m,
            t.region_id,
            ROUND(AVG(ST_Y(t1_survey.coords)), 7) AS surveys_centroid_lat,
            ROUND(AVG(ST_X(t1_survey.coords)), 7) AS surveys_centroid_lon,
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
            region_id
        )
        SELECT
            SUBSTR(TRIM('_' FROM REGEXP_REPLACE(taxon.scientific_name, '[^a-zA-Z]', '_')), 1, 40) AS Binomial,
            ROW_NUMBER() OVER () AS ID,
            MIN(CONCAT(t2.source_id, '_', t2.unit_id, '_', COALESCE(t2.search_type_id, '0'), '_', t2.site_id, '_', t2.taxon_id)) AS TimeSeriesID,
            source.id AS SourceID,
            source.description AS SourceDesc,
            (SELECT description FROM data_processing_type WHERE id = source.data_processing_type_id) AS DataProcessingType,
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
            t2.site_id AS SiteID,
            t1_site.name AS SiteName,
            region.state AS State,
            region.name AS Region,
            %s,
            MAX(t2.positional_accuracy_in_m) AS SurveysSpatialAccuracyInMetres,
            (SELECT description FROM search_type WHERE id = t2.search_type_id) AS SearchTypeDesc,
            (SELECT description FROM unit WHERE id = t2.unit_id) AS UnitOfMeasurement,
            (SELECT description FROM monitoring_program WHERE source.monitoring_program_id = monitoring_program.id) AS MonitoringProgram,
            COALESCE((SELECT type FROM management WHERE id = t1_site.management_id), "No known management") AS Management,
            COALESCE((SELECT description FROM management WHERE id = t1_site.management_id), "Unknown") AS ManagementCategory,
            %s,
            SUM(t2.survey_count) AS SurveyCount,
            MAX(start_date_y) - MIN(start_date_y) + 1 AS TimeSeriesLength,
            COUNT(DISTINCT start_date_y) AS TimeSeriesSampleYears,
            COUNT(DISTINCT start_date_y) / (MAX(start_date_y) - MIN(start_date_y) + 1) AS TimeSeriesCompleteness
        FROM t2
        JOIN taxon ON taxon.id = t2.taxon_id
        JOIN t1_site ON t1_site.id = t2.site_id
        JOIN source ON source.id = t2.source_id
        LEFT JOIN region ON region.id = t2.region_id
        GROUP BY
            t2.site_id,
            t2.taxon_id,
            t2.source_id,
            t2.unit_id,
            t2.search_type_id,
            t2.region_id
        %s
        """ % (raw_data_sql, coordinates_sql, year_fields_sql, random_sample_sql)

    return db_session.execute(text(sql), params)


def trend_work_dir(trend_id):
    return os.path.join(data_dir("processed_data"), "subset", trend_id)


lock = Lock()
processing_trend_ids = set()

def process_trend(trend_id):
    with lock:
        processing_trend_ids.add(trend_id)
    try:
        path = trend_work_dir(trend_id)

        script_params = [os.path.join(path, "lpi.csv"), path]

        try:
            with open(os.path.join(path, 'params.json')) as f:
                params_json = json.load(f)
                if 'reference_year' in params_json:
                    script_params.append(str(params_json['reference_year']))
                    if 'final_year' in params_json:
                        script_params.append(str(params_json['final_year']))
        except:
            pass

        script_params.append('--filter-rows')

        subprocess.run(["Rscript", os.path.join(path, "lpi.R")] + script_params)
        results_path = os.path.join(path, "data_infile_Results.txt")
        if os.path.exists(results_path):
            shutil.copy(results_path, os.path.join(path, "trend.txt"))
    finally:
        with lock:
            processing_trend_ids.remove(trend_id)

@bp.route('/subset/trend', methods = ['POST'])
def subset_generate_trend():
    trend_id, _ = subset_generate_trend_async()
    return jsonify({"id": trend_id}), 201

def subset_generate_trend_async(subset_params=None):
    trend_id = str(uuid4())

    path = trend_work_dir(trend_id)
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "lpi.R"), "wb") as f:
        f.write(importlib.resources.read_binary("tsx.resources", "lpi.R"))

    result = query_subset_time_series(subset_params)
    save_csv(result, os.path.join(path, "lpi.csv"))

    # Save subset parameters and extra trend parameters e.g. reference/final year
    args = get_request_args_or_body()
    trend_params = { **args, **(subset_params or {})}

    with open(os.path.join(path, "params.json"), "w") as f:
        json.dump(trend_params, f)

    thread = Thread(target = process_trend, args = (trend_id,))
    thread.start()

    return trend_id, thread

# Returns path to generated trend and time series
def subset_generate_trend_sync(subset_params):
    trend_id, thread = subset_generate_trend_async(subset_params)
    thread.join()
    work_dir = trend_work_dir(trend_id)

    return os.path.join(work_dir, "trend.txt"), os.path.join(work_dir, "lpi.csv")

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


def get_trend_params(trend_id):
    path = trend_work_dir(trend_id)
    try:
        with open(os.path.join(path, "params.json"), "r") as f:
            return json.load(f)
    except:
        return None

@bp.route('/subset/trend/<trend_id>')
def subset_get_trend(trend_id):
    path = os.path.join(trend_work_dir(trend_id), "trend.txt")
    if os.path.exists(path):
        with open(path, 'r') as file:
            raw_trend = file.read()
        result_format = request.args.get('format', default='raw', type=str)
        if result_format == 'raw':
            return Response(raw_trend, mimetype="text/plain")
        elif result_format == 'csv':
            params = get_trend_params(trend_id)
            if params:
                filename = 'tsx-trend&%s.csv' % filename_component_from_params(params)
            else:
                filename = 'tsx-trend-%s.csv' % trend_id

            trend_csv = trend_txt_to_csv(raw_trend)
            return Response(trend_csv, mimetype="text/csv", headers={
               "Content-Disposition": "attachment; filename=%s" % (filename)
            })
        else:
            return jsonify("Invalid format (Allowed formats: raw, csv)"), 400

    else:
        return "Not found", 404

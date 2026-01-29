from tsx.db import get_session
from tqdm import tqdm
import logging
from tsx.util import run_parallel, sql_list_placeholder, sql_list_argument
import time
import csv
import os
import tsx.config
from datetime import date
import re
import numpy as np
import tsx.config
import sys
from sqlalchemy import text

log = logging.getLogger(__name__)

try:
    if unicode:
        unicode_type_exists = True
except NameError:
    unicode_type_exists = False

def process_database(species = None, monthly = False, filter_output = False, include_all_years_data = False, database_config = None, export_dir = None):
    session = get_session(database_config)

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute(text("SELECT DISTINCT taxon_id FROM aggregated_by_year")).fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
                text("SELECT DISTINCT taxon_id FROM aggregated_by_year, taxon WHERE taxon.id = taxon_id AND spno IN (%s)" % sql_list_placeholder('species', species)),
                sql_list_argument('species', species)
            ).fetchall()]

    log.info("Checking time_series_inclusion is consistent")

    result = list(session.execute(text("""
        WITH agg AS (
            SELECT time_series_id, MAX(include_in_analysis) AS include_in_analysis
            FROM aggregated_by_year
            GROUP BY time_series_id
        )
        SELECT
            (SELECT COUNT(*) FROM agg) = (SELECT COUNT(*) FROM time_series_inclusion)
            AND
            (
                SELECT COUNT(*)
                FROM agg
            ) = (
                SELECT COUNT(*)
                FROM agg
                JOIN time_series_inclusion inc
                ON agg.time_series_id = inc.time_series_id
                WHERE agg.include_in_analysis = inc.include_in_analysis
            );
        """)))

    if result != [(1,)]:
        log.error("time_series_inclusion is not consistent with aggregated_by_year table")
        log.info("Make sure you have run python -m tsx.process -c filter_time_series before attempting to export")
        sys.exit(1)

    log.info("Calculating region centroids")

    session.execute(text("""CREATE TEMPORARY TABLE region_centroid AS
        -- (PRIMARY KEY (id))
        SELECT id, ST_X(ST_Centroid(geometry)) AS x, ST_Y(ST_Centroid(geometry)) AS y
        FROM region"""))

    # Get year range
    min_year = tsx.config.config.getint("processing", "min_year")
    max_analysis_year = tsx.config.config.getint("processing", "max_year")
    min_tssy = tsx.config.config.getint("processing", "min_time_series_sample_years")

    # When enabled, this flag means that all year's data will be included for any time series that passed filtering,
    # even beyond the max_year specified in the config file. However, the TimeSeriesSampleYears and other stats still
    # need to reflect only the years up to max_year, so it makes things a tad more complicated.
    if include_all_years_data:
        (max_year,) = session.execute(text("""SELECT MAX(start_date_y) FROM aggregated_by_year""")).fetchone()
    else:
        max_year = max_analysis_year


    # Without this, the GROUP_CONCAT in the export query produces rows that are too long
    if database_config == None or "sqlite:" not in database_config:
        session.execute(text("""SET SESSION group_concat_max_len = 50000;"""))

    export_dir = export_dir or tsx.config.data_dir('export')

    filename = 'lpi'
    if monthly:
        filename += '-monthly'
    if filter_output:
        filename += '-filtered'
    if include_all_years_data:
        filename += '-all-years'
    filename += '.csv'

    filepath = os.path.join(export_dir, filename)

    log.info("Exporting LPI wide table file: %s" % filepath)

    with open(filepath, 'w', encoding='utf-8') as csvfile:
        fieldnames = [
            'ID',
            'Binomial',
            'SpNo',
            'TaxonID',
            'CommonName',
            'Class',
            'Order',
            'Family',
            'FamilyCommonName',
            'Genus',
            'Species',
            'Subspecies',
            'FunctionalGroup',
            # 'FunctionalSubGroup',
            'TaxonomicGroup',
            'EPBCStatus',
            'IUCNStatus',
            'StatePlantStatus',
            'BirdActionPlanStatus',
            'MaxStatus',
            'State',
            'Region',
            'RegionCentroidLatitude',
            'RegionCentroidLongitude',
            'RegionCentroidAccuracy',
            'SiteID',
            'SiteName',
            'SourceID',
            'SourceDesc',
            'MonitoringProgram',
            'UnitID',
            'Unit',
            'SearchTypeID',
            'SearchTypeDesc',
            'ResponseVariableType',
            'DataType'
        ]

        if monthly:
            fieldnames += ["%s_%02d" % (year, month) for year in range(min_year, max_year + 1) for month in range(0, 13)]
        else:
            fieldnames += [str(year) for year in range(min_year, max_year + 1)]

        fieldnames += [
            'TimeSeriesLength',
            'TimeSeriesSampleYears',
            'TimeSeriesCompleteness',
            'TimeSeriesSamplingEvenness',
            'AbsencesRecorded',
            'StandardisationOfMethodEffort',
            'ObjectiveOfMonitoring',
            'SpatialRepresentativeness',
            'ConsistencyOfMonitoring',
            'Management',
            'ManagementCategory',
            'ManagementCategoryComments',
            'DataAgreement',
            'SuppressAggregatedData',
            'SurveysCentroidLatitude',
            'SurveysCentroidLongitude',
            'SurveysSpatialAccuracy',
            'SurveyCount',
            'TimeSeriesID',
            'InclusionCategory',
            'InclusionCategoryComments',
            'NationalPriorityTaxa',
            'Citation'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        where_conditions = []
        having_clause = ''

        if filter_output:
            if include_all_years_data:
                having_clause = "HAVING MAX(agg.include_in_analysis)"
            else:
                where_conditions += ['agg.include_in_analysis']

        if monthly:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '_', LPAD(COALESCE(start_date_m, 0), 2, '0'), '=', value))"
            aggregated_table = 'aggregated_by_month'
        else:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '=', value))"
            aggregated_table = 'aggregated_by_year'

        index = 1

        for taxon_id in tqdm(taxa):
            #                    (SELECT CAST(id AS UNSIGNED) FROM aggregated_id agg_id WHERE agg.taxon_id = agg_id.taxon_id AND agg.search_type_id <=> agg_id.search_type_id AND agg.source_id = agg_id.source_id AND agg.unit_id = agg_id.unit_id AND agg.site_id <=> agg_id.site_id AND agg.data_type = agg_id.data_type) AS ID,
            sql = """SELECT
                    agg.time_series_id AS TimeSeriesID,
                    taxon.spno AS SpNo,
                    taxon.id AS TaxonID,
                    taxon.common_name AS CommonName,
                    taxon.`order` AS `Order`,
                    taxon.scientific_name AS scientific_name,
                    taxon.family_scientific_name AS Family,
                    taxon.family_common_name AS FamilyCommonName,
                    (SELECT
                        GROUP_CONCAT(
                            CONCAT(taxon_group.group_name, COALESCE(CONCAT(':', taxon_group.subgroup_name), ''))
                        )
                        FROM taxon_group
                        WHERE taxon_group.taxon_id = taxon.id
                    ) AS FunctionalGroup,
                    taxon.taxonomic_group AS TaxonomicGroup,
                    CASE taxon.taxonomic_group
                        WHEN 'Birds' THEN 'Aves'
                        WHEN 'Mammals' THEN 'Mammalia'
                        ELSE ''
                    END AS Class,
                    taxon.national_priority AS NationalPriorityTaxa,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.epbc_status_id) AS EPBCStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.iucn_status_id) AS IUCNStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.state_status_id) AS StatePlantStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.bird_action_plan_status_id) AS BirdActionPlanStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.max_status_id) AS MaxStatus,
                    search_type.id AS SearchTypeID,
                    search_type.description AS SearchTypeDesc,
                    site_id AS SiteID,
                    COALESCE(
                        t1_site.name,
                        t2_site.name,
                        CONCAT('site_', agg.data_type, '_', site_id)
                    ) AS SiteName,
                    COALESCE((SELECT type FROM management WHERE t1_site.management_id = management.id), 'No known management') AS Management,
                    COALESCE((SELECT description FROM management WHERE t1_site.management_id = management.id), 'Unknown') AS ManagementCategory,
                    t1_site.management_comments AS ManagementCategoryComments,
                    source.id AS SourceID,
                    source.description AS SourceDesc,
                    (SELECT description FROM monitoring_program WHERE source.monitoring_program_id = monitoring_program.id) AS MonitoringProgram,
                    unit.id AS UnitID,
                    unit.description AS Unit,
                    region.name AS Region,
                    region.state AS State,
                    MIN(region_centroid.x) AS RegionCentroidLongitude,
                    MIN(region_centroid.y) AS RegionCentroidLatitude,
                    region.positional_accuracy_in_m AS RegionCentroidAccuracy,
                    {value_series} AS value_series,
                    COUNT(*) AS value_count,
                    agg.data_type AS DataType,
                    (SELECT description FROM response_variable_type WHERE agg.response_variable_type_id = response_variable_type.id) AS ResponseVariableType,
                    (CASE WHEN taxon.suppress_spatial_representativeness AND alpha.core_range_area_in_m2 THEN NULL ELSE ROUND(alpha.alpha_hull_area_in_m2 / alpha.core_range_area_in_m2, 4) END) AS SpatialRepresentativeness,
                    data_source.absences_recorded AS AbsencesRecorded,
                    data_source.standardisation_of_method_effort_id AS StandardisationOfMethodEffort,
                    data_source.objective_of_monitoring_id AS ObjectiveOfMonitoring,
                    data_source.consistency_of_monitoring_id AS ConsistencyOfMonitoring,
                    (SELECT description FROM data_agreement_status WHERE id = source.data_agreement_status_id) AS DataAgreement,
                    data_source.suppress_aggregated_data AS SuppressAggregatedData,
                    MAX(ST_X(agg.centroid_coords)) AS SurveysCentroidLongitude,
                    MAX(ST_Y(agg.centroid_coords)) AS SurveysCentroidLatitude,
                    MAX(agg.positional_accuracy_in_m) AS SurveysSpatialAccuracy,
                    SUM(agg.survey_count) AS SurveyCount,
                    (CASE WHEN time_series_inclusion.include_in_analysis THEN 'Included' ELSE 'Excluded' END) AS InclusionCategory,
                    TRIM(TRAILING '; ' FROM CONCAT(
                        IF(time_series_inclusion.sample_years, '',
                            'Sample years less than {min_tssy}; '),
                        IF(time_series_inclusion.master_list_include, '',
                            'Master List as Not In Index; '),
                        IF(time_series_inclusion.search_type, '',
                            'Search Type is Incidental'),
                        IF(time_series_inclusion.taxon_status, '',
                            'Status not NT/VU/EN/CR; '),
                        IF(time_series_inclusion.region, '',
                            'Region is NA; '),
                        IF(time_series_inclusion.data_agreement, '',
                            'Data agreement status excluded; '),
                        IF(time_series_inclusion.standardisation_of_method_effort, '',
                            'StandardisationOfMethodEffort is 0 or 1; '),
                        IF(time_series_inclusion.consistency_of_monitoring, '',
                            'ConsistencyOfMonitoring is 0 or 1; '),
                        IF(time_series_inclusion.non_zero, '',
                            'All values are 0; ')
                    )) AS InclusionCategoryComments,
                    CONCAT(
                        source.authors,
                        ' (', YEAR(NOW()), '). ',
                        TRIM(TRAILING '.' FROM TRIM(source.details)), '. ',
                        TRIM(TRAILING '.' FROM TRIM(source.provider)), '. ',
                        'Aggregated for the Australian Threatened Species Index, an output of the NESP Threatened Species Recovery Hub and operated by the Terrestrial Ecosystem Research Network, The University of Queensland.'
                    ) AS Citation
                FROM
                    {aggregated_table} agg
                    INNER JOIN taxon ON taxon.id = agg.taxon_id
                    INNER JOIN time_series_inclusion ON time_series_inclusion.time_series_id = agg.time_series_id
                    LEFT JOIN data_source_excluded_years ey ON ey.taxon_id = agg.taxon_id AND ey.source_id = agg.source_id AND ey.year = agg.start_date_y
                    LEFT JOIN search_type ON search_type.id = agg.search_type_id
                    INNER JOIN source ON source.id = agg.source_id
                    INNER JOIN unit ON unit.id = agg.unit_id
                    LEFT JOIN region ON region.id = agg.region_id
                    LEFT JOIN region_centroid ON region_centroid.id = agg.region_id
                    LEFT JOIN taxon_source_alpha_hull alpha ON alpha.taxon_id = agg.taxon_id AND alpha.source_id = agg.source_id AND alpha.data_type = agg.data_type
                    LEFT JOIN data_source_merged AS data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
                    LEFT JOIN t1_site ON site_id = t1_site.id AND agg.data_type = 1
                    LEFT JOIN t2_site ON site_id = t2_site.id AND agg.data_type = 2
                WHERE agg.taxon_id = :taxon_id
                AND start_date_y >= GREATEST(COALESCE(data_source.start_year, :min_year), :min_year)
                AND start_date_y <= LEAST(COALESCE(data_source.end_year, :max_year), :max_year)
                AND ey.year IS NULL
                {where_conditions}
                GROUP BY
                    agg.source_id,
                    agg.search_type_id,
                    agg.site_id,
                    agg.response_variable_type_id,
                    agg.region_id,
                    agg.unit_id,
                    agg.data_type
                {having_clause}
                ORDER BY
                    agg.source_id,
                    agg.search_type_id,
                    agg.site_id,
                    agg.response_variable_type_id,
                    agg.region_id,
                    agg.unit_id,
                    agg.data_type
                    """.format(
                        value_series = value_series,
                        aggregated_table = aggregated_table,
                        where_conditions = " ".join("AND %s" % cond for cond in where_conditions),
                        having_clause = having_clause,
                        min_tssy = min_tssy
                    )

            result = session.execute(text(sql), {
                        'taxon_id': taxon_id,
                        'min_year': min_year,
                        'max_year': max_year
                    })

            keys = result.keys()

            for row in result.fetchall():
                # Get row as a dict
                data = dict(zip(keys, row))

                data["ID"] = index
                index += 1

                # Parse out the yearly values (or monthly)
                year_data = dict(item.split('=') for item in data['value_series'].split(','))

                if len(year_data) != data['value_count']:
                    raise ValueError("Aggregation problem - number of years/months in value series (%s) does not match expected value count (%s)" % (len(year_data), data['value_count']))

                # Populate years in output
                data.update(year_data)

                # Taxonomic columns
                data['Binomial'] = re.sub(r'[^A-Za-z]+', '_', data['scientific_name']).strip('_')[0:40]
                name_parts = data['scientific_name'].split(' ', 2)
                data['Genus'] = name_parts[0]
                if len(name_parts) > 1:
                    data['Species'] = name_parts[1]
                if len(name_parts) > 2:
                    data['Subspecies'] = name_parts[2]

                # Calculate temporal suitability metrics:

                if not monthly and len(year_data) > 0:
                    years = sorted([int(year) for year in year_data.keys()])

                    # If we include all years' data, we still want to output stats as if we were only processing up to max_analysis_year
                    if include_all_years_data:
                        years = list(filter(lambda y: y <= max_analysis_year, years))

                    # Due to previous step, years could in fact be empty by this point
                    if len(years) > 0:
                        year_range = max(years) - min(years) + 1

                        data['TimeSeriesLength'] = year_range
                        data['TimeSeriesSampleYears'] = len(years)
                        data['TimeSeriesCompleteness'] = "%0.3f" % (float(len(years)) / year_range)

                        # Get all non-zero gaps between years
                        gaps = [b - a - 1 for a, b in zip(years[:-1], years[1:]) if b - a > 1]
                        data['TimeSeriesSamplingEvenness'] = np.array(gaps).var() if len(gaps) > 0 else 0

                # Remove unwanted key from dict
                del data['value_series']
                del data['value_count']
                del data['scientific_name']

                if unicode_type_exists:
                    writer.writerow({k: None if v == None else unicode(v).encode("utf-8") for k, v in data.items()})
                else:
                    writer.writerow({k: None if v == None else str(v) for k, v in data.items()})

    log.info("Done")

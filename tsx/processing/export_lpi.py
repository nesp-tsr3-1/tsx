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

log = logging.getLogger(__name__)

try:
    if unicode:
        unicode_type_exists = True
except NameError:
    unicode_type_exists = False

def process_database(species = None, monthly = False, filter_output = False, include_all_years_data = False, database_config = None, export_dir = None):
    session = get_session(database_config)

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM aggregated_by_year").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
                "SELECT DISTINCT taxon_id FROM aggregated_by_year, taxon WHERE taxon.id = taxon_id AND spno IN (%s)" % sql_list_placeholder('species', species),
                sql_list_argument('species', species)
            ).fetchall()]

    log.info("Generating numeric IDs")

    # Create stable IDs for each taxon_id / search_type_id / source_id / unit_id / site_id / data_type combination
    # session.execute("""CREATE TEMPORARY TABLE aggregated_id
    #     ( INDEX (taxon_id, search_type_id, source_id, unit_id, site_id, grid_cell_id, data_type) )
    #     SELECT (@cnt := @cnt + 1) AS id, taxon_id, search_type_id, source_id, unit_id, site_id, grid_cell_id, data_type
    #     FROM (SELECT DISTINCT taxon_id, search_type_id, source_id, unit_id, site_id, grid_cell_id, data_type FROM aggregated_by_year) t
    #     CROSS JOIN (SELECT @cnt := 0) AS dummy""")

    log.info("Calculating region centroids")

    session.execute("""CREATE TEMPORARY TABLE region_centroid AS
        -- (PRIMARY KEY (id))
        SELECT id, ST_X(ST_Centroid(geometry)) AS x, ST_Y(ST_Centroid(geometry)) AS y
        FROM region""")

    # Get year range
    min_year = tsx.config.config.getint("processing", "min_year")
    max_analysis_year = tsx.config.config.getint("processing", "max_year")

    # When enabled, this flag means that all year's data will be included for any time series that passed filtering,
    # even beyond the max_year specified in the config file. However, the TimeSeriesSampleYears and other stats still
    # need to reflect only the years up to max_year, so it makes things a tad more complicated.
    if include_all_years_data:
        (max_year,) = session.execute("""SELECT MAX(start_date_y) FROM aggregated_by_year""").fetchone()
    else:
        max_year = max_analysis_year


    # Without this, the GROUP_CONCAT in the export query produces rows that are too long
    if database_config and "sqlite:" not in database_config:
        session.execute("""SET SESSION group_concat_max_len = 50000;""")

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
            'MaxStatus',
            'State',
            'Region',
            'RegionCentroidLatitude',
            'RegionCentroidLongitude',
            'RegionCentroidAccuracy',
            'SiteID',
            'SiteDesc',
            'SourceID',
            'SourceDesc',
            'MonitoringProgram',
            'UnitID',
            'Unit',
            'SearchTypeID',
            'SearchTypeDesc',
            'ExperimentalDesignType',
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
            # 'SeasonalConsistency', # TBD
            'ConsistencyOfMonitoring',
            # 'MonitoringFrequencyAndTiming', # TBD
            'IntensiveManagement',
            'IntensiveManagementGrouping',
            'DataAgreement',
            'SuppressAggregatedData',
            'SurveysCentroidLatitude',
            'SurveysCentroidLongitude',
            'SurveysSpatialAccuracy',
            'SurveyCount',
            'TimeSeriesID',
            'NationalPriorityTaxa',
            'Citation'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        where_conditions = []
        having_clause = ''

        if filter_output:
            if include_all_years_data:
                having_clause = "HAVING MAX(include_in_analysis)"
            else:
                where_conditions += ['include_in_analysis']

        if monthly:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '_', LPAD(COALESCE(start_date_m, 0), 2, '0'), '=', value))"
            aggregated_table = 'aggregated_by_month'
        else:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '=', value))"
            aggregated_table = 'aggregated_by_year'

        if database_config and "sqlite:" in database_config:
            current_date_expression = "DATE('NOW')"
            current_year_expression = "strftime('%Y', 'now')"
        else:
            current_date_expression = "DATE(NOW())"
            current_year_expression = "YEAR(NOW())"

        index = 1

        for taxon_id in tqdm(taxa):
            #                    (SELECT CAST(id AS UNSIGNED) FROM aggregated_id agg_id WHERE agg.taxon_id = agg_id.taxon_id AND agg.search_type_id <=> agg_id.search_type_id AND agg.source_id = agg_id.source_id AND agg.unit_id = agg_id.unit_id AND agg.site_id <=> agg_id.site_id AND agg.grid_cell_id <=> agg_id.grid_cell_id AND agg.data_type = agg_id.data_type) AS ID,
            sql = """SELECT
                    time_series_id AS TimeSeriesID,
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
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.max_status_id) AS MaxStatus,
                    search_type.id AS SearchTypeID,
                    search_type.description AS SearchTypeDesc,
                    COALESCE(site_id, grid_cell_id) AS SiteID,
                    COALESCE(
                        t1_site.name,
                        t2_site.name,
                        CONCAT('site_', agg.data_type, '_', site_id),
                        CONCAT('grid_', grid_cell_id)) AS SiteDesc,
                    (SELECT description FROM intensive_management WHERE t1_site.intensive_management_id = intensive_management.id) AS IntensiveManagement,
                    (SELECT `grouping` FROM intensive_management WHERE t1_site.intensive_management_id = intensive_management.id) AS IntensiveManagementGrouping,
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
                    (SELECT description FROM experimental_design_type WHERE agg.experimental_design_type_id = experimental_design_type.id) AS ExperimentalDesignType,
                    (SELECT description FROM response_variable_type WHERE agg.response_variable_type_id = response_variable_type.id) AS ResponseVariableType,
                    (CASE WHEN taxon.suppress_spatial_representativeness THEN NULL ELSE ROUND(alpha.alpha_hull_area_in_m2 / alpha.core_range_area_in_m2, 4) END) AS SpatialRepresentativeness,
                    data_source.absences_recorded AS AbsencesRecorded,
                    data_source.standardisation_of_method_effort_id AS StandardisationOfMethodEffort,
                    data_source.objective_of_monitoring_id AS ObjectiveOfMonitoring,
                    data_source.consistency_of_monitoring_id AS ConsistencyOfMonitoring,
                    data_source.data_agreement_id AS DataAgreement,
                    data_source.suppress_aggregated_data AS SuppressAggregatedData,
                    MAX(ST_X(agg.centroid_coords)) AS SurveysCentroidLongitude,
                    MAX(ST_Y(agg.centroid_coords)) AS SurveysCentroidLatitude,
                    MAX(agg.positional_accuracy_in_m) AS SurveysSpatialAccuracy,
                    SUM(agg.survey_count) AS SurveyCount,
                    CONCAT(
                        COALESCE(CONCAT(source.authors, ' '), ''),
                        '(', {current_year_expression}, '). ',
                        COALESCE(CONCAT(source.description, '. '), ''),
                        COALESCE(CONCAT(source.provider, '. '), ''),
                        'Aggregated for National Environmental Science Program Threatened Species Recovery Hub Project 3.1. Generated on ',
                        {current_date_expression}
                    ) AS Citation
                FROM
                    {aggregated_table} agg
                    INNER JOIN taxon ON taxon.id = agg.taxon_id
                    LEFT JOIN search_type ON search_type.id = agg.search_type_id
                    INNER JOIN source ON source.id = agg.source_id
                    INNER JOIN unit ON unit.id = agg.unit_id
                    LEFT JOIN region ON region.id = agg.region_id
                    LEFT JOIN region_centroid ON region_centroid.id = agg.region_id
                    LEFT JOIN taxon_source_alpha_hull alpha ON alpha.taxon_id = agg.taxon_id AND alpha.source_id = agg.source_id AND alpha.data_type = agg.data_type
                    LEFT JOIN data_source ON data_source.taxon_id = agg.taxon_id AND data_source.source_id = agg.source_id
                    LEFT JOIN t1_site ON site_id = t1_site.id AND agg.data_type = 1
                    LEFT JOIN t2_site ON site_id = t2_site.id AND agg.data_type = 2
                WHERE agg.taxon_id = :taxon_id
                AND start_date_y >= :min_year
                AND start_date_y <= :max_year
                {where_conditions}
                GROUP BY
                    agg.source_id,
                    agg.search_type_id,
                    agg.site_id,
                    agg.grid_cell_id,
                    agg.experimental_design_type_id,
                    agg.response_variable_type_id,
                    agg.region_id,
                    agg.unit_id,
                    agg.data_type
                ORDER BY
                    agg.source_id,
                    agg.search_type_id,
                    agg.site_id,
                    agg.grid_cell_id,
                    agg.experimental_design_type_id,
                    agg.response_variable_type_id,
                    agg.region_id,
                    agg.unit_id,
                    agg.data_type
                {having_clause}
                    """.format(
                        value_series = value_series,
                        aggregated_table = aggregated_table,
                        where_conditions = " ".join("AND %s" % cond for cond in where_conditions),
                        having_clause = having_clause,
                        current_date_expression = current_date_expression,
                        current_year_expression = current_year_expression
                    )

            result = session.execute(sql, {
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
                    raise ValueError("Aggregation problem - duplicate years found in time series: %s" % row)

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

from nesp.db import get_session
from tqdm import tqdm
import logging
from nesp.util import run_parallel
import time
import csv
import os
import nesp.config
from datetime import date
import re
import numpy as np

log = logging.getLogger(__name__)

def process_database(species = None, monthly = False):
    session = get_session()

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM aggregated_by_year").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            "SELECT DISTINCT taxon_id FROM aggregated_by_year, taxon WHERE taxon.id = taxon_id AND spno IN :species", {
                'species': species
            }).fetchall()]

    log.info("Generating numeric IDs")

    # Create stable IDs for each taxon_id / search_type_id / source_id / unit_id / site_id / data_type combination
    session.execute("""CREATE TEMPORARY TABLE aggregated_id
        ( INDEX (taxon_id, search_type_id, source_id, unit_id, site_id, data_type) )
        SELECT (@cnt := @cnt + 1) AS id, taxon_id, search_type_id, source_id, unit_id, site_id, data_type
        FROM (SELECT DISTINCT taxon_id, search_type_id, source_id, unit_id, site_id, data_type FROM aggregated_by_year) t
        CROSS JOIN (SELECT @cnt := 0) AS dummy""")

    log.info("Calculating region centroids")

    session.execute("""CREATE TEMPORARY TABLE region_centroid
        (PRIMARY KEY (id))
        SELECT id, ST_X(ST_Centroid(geometry)) AS x, ST_Y(ST_Centroid(geometry)) AS y
        FROM region""")

    # Get year range
    # TODO: Read min year from config file
    min_year, max_year = 1950, date.today().year + 1

    # Without this, the GROUP_CONCAT in the export query produces rows that are too long
    session.execute("""SET SESSION group_concat_max_len = 50000;""")

    export_dir = nesp.config.data_dir('export')
    filename = 'lpi-monthly.csv' if monthly else 'lpi.csv'
    filepath = os.path.join(export_dir, filename)

    log.info("Exporting LPI wide table file: %s" % filepath)

    with open(filepath, 'w') as csvfile:
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
            'FunctionalSubGroup',
            'EPBCStatus',
            'IUCNStatus',
            'BirdLifeAustraliaStatus',
            'MaxStatus',
            'State',
            'Region',
            'Latitude',
            'Longitude',
            'SiteID',
            'SiteDesc',
            'SourceID',
            'SourceDesc',
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
            'NoAbsencesRecorded', # TBD
            'StandardisationOfMethodEffort', # TBD
            'ObjectiveOfMonitoring', # TBD
            'SpatialRepresentativeness',
            'SeasonalConsistency', # TBD
            'SpatialAccuracy',
            'ConsistencyOfMonitoring', # TBD
            'MonitoringFrequencyAndTiming', # TBD
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        where_conditions = []

        if monthly:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '_', LPAD(COALESCE(start_date_m, 0), 2, '0'), '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_month'
        else:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_year'

        for taxon_id in tqdm(taxa):
            sql = """SELECT
                    (SELECT CAST(id AS UNSIGNED) FROM aggregated_id agg_id WHERE agg.taxon_id = agg_id.taxon_id AND agg.search_type_id = agg_id.search_type_id AND agg.source_id = agg_id.source_id AND agg.unit_id = agg_id.unit_id AND agg.site_id = agg_id.site_id AND agg.data_type = agg_id.data_type) AS ID,
                    taxon.spno AS SpNo,
                    taxon.id AS TaxonID,
                    taxon.common_name AS CommonName,
                    taxon.order AS `Order`,
                    taxon.scientific_name AS scientific_name,
                    taxon.family_scientific_name AS Family,
                    taxon.family_common_name AS FamilyCommonName,
                    taxon.bird_group AS FunctionalGroup,
                    taxon.bird_sub_group AS FunctionalSubGroup,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.epbc_status_id) AS EPBCStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.iucn_status_id) AS IUCNStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.aust_status_id) AS BirdLifeAustraliaStatus,
                    (SELECT description FROM taxon_status WHERE taxon_status.id =
                        GREATEST(COALESCE(taxon.epbc_status_id, 0), COALESCE(taxon.iucn_status_id, 0), COALESCE(taxon.aust_status_id, 0))) AS MaxStatus,
                    search_type.id AS SearchTypeID,
                    search_type.description AS SearchTypeDesc,
                    COALESCE(site_id, grid_cell_id) AS SiteID,
                    COALESCE(
                        (SELECT name FROM t1_site WHERE site_id = t1_site.id AND agg.data_type = 1),
                        (SELECT name FROM t2_site WHERE site_id = t2_site.id AND agg.data_type = 2),
                        CONCAT('site_', agg.data_type, '_', site_id),
                        CONCAT('grid_', grid_cell_id)) AS SiteDesc,
                    source.id AS SourceID,
                    source.description AS SourceDesc,
                    unit.id AS UnitID,
                    unit.description AS Unit,
                    region.name AS Region,
                    region.state AS State,
                    region_centroid.x AS Longitude,
                    region_centroid.y AS Latitude,
                    MAX(positional_accuracy_in_m) AS SpatialAccuracy,
                    {value_series} AS value_series,
                    agg.data_type AS DataType,
                    (SELECT description FROM experimental_design_type WHERE agg.experimental_design_type_id = experimental_design_type.id) AS ExperimentalDesignType,
                    (SELECT description FROM response_variable_type WHERE agg.response_variable_type_id = response_variable_type.id) AS ResponseVariableType,
                    COALESCE(ROUND(alpha.alpha_hull_area_in_m2 / alpha.core_range_area_in_m2, 4), 0) AS SpatialRepresentativeness
                FROM
                    {aggregated_table} agg
                    INNER JOIN taxon ON taxon.id = taxon_id
                    INNER JOIN source ON source.id = source_id
                    INNER JOIN unit ON unit.id = unit_id
                    LEFT JOIN search_type ON search_type.id = search_type_id
                    LEFT JOIN region ON region.id = region_id
                    LEFT JOIN region_centroid ON region_centroid.id = region_id
                    LEFT JOIN taxon_source_alpha_hull alpha ON alpha.taxon_id = agg.taxon_id AND alpha.source_id = agg.source_id AND alpha.data_type = agg.data_type
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
                    """.format(
                        value_series = value_series,
                        aggregated_table = aggregated_table,
                        where_conditions = " ".join("AND %s" % cond for cond in where_conditions)
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

                # Parse out the yearly values (or monthly)
                year_data = dict(item.split('=') for item in data['value_series'].split(','))

                # Populate years in output
                data.update(year_data)

                # Taxonomic columns
                data['Binomial'] = re.sub(r'[^\w]', '_', data['CommonName'])
                data['Class'] = 'Aves'
                name_parts = data['scientific_name'].split(' ')
                data['Genus'] = name_parts[0]
                if len(name_parts) > 1:
                    data['Species'] = name_parts[1]
                if len(name_parts) > 2:
                    data['Subspecies'] = name_parts[2]

                # Calculate temporal suitability metrics:

                if not monthly and len(year_data) > 0:
                    years = sorted([int(year) for year in year_data.keys()])
                    year_range = max(years) - min(years) + 1

                    data['TimeSeriesLength'] = year_range
                    data['TimeSeriesSampleYears'] = len(years)
                    data['TimeSeriesCompleteness'] = "%0.3f" % (float(len(years)) / year_range)

                    # Get all non-zero gaps between years
                    gaps = [b - a - 1 for a, b in zip(years[:-1], years[1:]) if b - a > 1]
                    data['TimeSeriesSamplingEvenness'] = np.array(gaps).var() if len(gaps) > 0 else 0

                # Remove unwanted key from dict
                del data['value_series']
                del data['scientific_name']

                writer.writerow(data)

    log.info("Done")

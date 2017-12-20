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

    # Create stable IDs for each taxon_id / search_type_id / source_id / unit_id / site_id / data_type combination
    session.execute("""CREATE TEMPORARY TABLE aggregated_id
        ( INDEX (taxon_id, search_type_id, source_id, unit_id, site_id, data_type) )
        SELECT (@cnt := @cnt + 1) AS id, taxon_id, search_type_id, source_id, unit_id, site_id, data_type
        FROM (SELECT DISTINCT taxon_id, search_type_id, source_id, unit_id, site_id, data_type FROM aggregated_by_year) t
        CROSS JOIN (SELECT @cnt := 0) AS dummy""")

    # Get year range
    # TODO: Read min year from config file
    min_year, max_year = 1950, date.today().year + 1

    # Without this, the GROUP_CONCAT in the export query produces rows that are too long
    session.execute("""SET SESSION group_concat_max_len = 50000;""")

    export_dir = nesp.config.data_dir('export')
    filename = 'lpi-monthly.csv' if monthly else 'lpi.csv'

    with open(os.path.join(export_dir, filename), 'w') as csvfile:
        fieldnames = [
            'ID',
            'Binomial',
            'SpNo',
            'TaxonID',
            'CommonName',
            #  Class, Order, Family, Genus, Species, Subspecies # TBD
            'FunctionalSubGroup', # TBD
            'EPBCStatus' # TBD
            'IUCNStatus', # TBD
            'BirdLifeAustStatus', # TBD
            'MaxStatus', # TBD
            'State',
            'SubIBRA',
            'Latitude', # TBD
            'Longitude', # TBD
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
            fieldnames += ["%s_%02d" % (year, month) for year in range(min_year, max_year + 1) for month in range(1, 13)]
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
            #'OtherEvenenessThingys',
            'SpatialAccuracyInM',
            'ConsistencyOfMonitoring', # TBD
            'MonitoringFrequencyAndTiming' # TBD
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        where_conditions = []

        if monthly:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '_', LPAD(start_date_m, 2, '0'), '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_month'
            where_conditions.append('start_date_m IS NOT NULL')
        else:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_year'

        for taxon_id in tqdm(taxa):
            sql = """SELECT
                    (SELECT CAST(id AS UNSIGNED) FROM aggregated_id agg_id WHERE agg.taxon_id = agg_id.taxon_id AND agg.search_type_id = agg_id.search_type_id AND agg.source_id = agg_id.source_id AND agg.unit_id = agg_id.unit_id AND agg.site_id = agg_id.site_id AND agg.data_type = agg_id.data_type) AS ID,
                    taxon.spno AS SpNo,
                    taxon.id AS TaxonID,
                    taxon.common_name AS CommonName,
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
                    region.name AS SubIBRA,
                    region.state AS State,
                    MAX(positional_accuracy_in_m) AS SpatialAccuracyInM,
                    {value_series} AS value_series,
                    agg.data_type AS DataType,
                    (SELECT description FROM experimental_design_type WHERE agg.experimental_design_type_id = experimental_design_type.id) AS ExperimentalDesignType,
                    (SELECT description FROM response_variable_type WHERE agg.response_variable_type_id = response_variable_type.id) AS ResponseVariableType,
                    COALESCE(ROUND(alpha.alpha_hull_area_in_m2 / alpha.core_range_area_in_m2, 4), 0) AS SpatialRepresentativeness
                FROM
                    {aggregated_table} agg
                    INNER JOIN taxon ON taxon.id = taxon_id
                    INNER JOIN search_type ON search_type.id = search_type_id
                    INNER JOIN source ON source.id = source_id
                    INNER JOIN unit ON unit.id = unit_id
                    LEFT JOIN region ON region.id = region_id
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

                # Parse out the yearly values
                year_data = dict(item.split('=') for item in data['value_series'].split(','))

                # Populate years in output
                data.update(year_data)

                data['Binomial'] = re.sub(r'[^\w]', '_', data['CommonName'])

                # Calculate temporal suitability metrics:

                if len(year_data) > 0:
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

                writer.writerow(data)

    log.info("Done")

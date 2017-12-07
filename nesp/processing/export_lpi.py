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

log = logging.getLogger(__name__)

def process_database(species = None, monthly = False):
    session = get_session()

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM aggregated_by_year").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            "SELECT DISTINCT taxon_id FROM t2_processed_sighting, taxon WHERE taxon.id = taxon_id AND spno IN :species", {
                'species': species
            }).fetchall()]

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
            'SiteDesc',
            'SourceDesc',
            'SubIBRA',
            'State',
            'Unit',
            'SearchTypeDesc',
            # 'TimeSeriesLength',
            # 'TimeSeriesCompleteness',
            'SpatialAccuracyInM',
            'ExperimentalDesignType',
            'ResponseVariableType',
            'DataType'
            # 'TaxonSpatialRepresentativeness'
        ]

        if monthly:
            fieldnames += ["%s_%02d" % (year, month) for year in range(min_year, max_year + 1) for month in range(1, 13)]
        else:
            fieldnames += [str(year) for year in range(min_year, max_year + 1)]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        i = 1

        if monthly:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '_', LPAD(start_date_m, 2, '0'), '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_month'
        else:
            value_series = "GROUP_CONCAT(CONCAT(start_date_y, '=', value) ORDER BY start_date_y)"
            aggregated_table = 'aggregated_by_year'

        for taxon_id in tqdm(taxa):
            # Note we select units based on response variable type id
            sql = """SELECT
                    taxon.spno AS SpNo,
                    taxon.id AS TaxonID,
                    taxon.common_name AS CommonName,
                    search_type.description AS SearchTypeDesc,
                    COALESCE(
                        (SELECT name FROM t1_site WHERE site_id = t1_site.id AND data_type = 1),
                        (SELECT name FROM t2_site WHERE site_id = t2_site.id AND data_type = 2),
                        CONCAT('site_', data_type, '_', site_id),
                        CONCAT('grid_', grid_cell_id)) AS SiteDesc,
                    source.description AS SourceDesc,
                    unit.description AS Unit,
                    region.name AS SubIBRA,
                    region.state AS State,
                    MAX(positional_accuracy_in_m) AS SpatialAccuracyInM,
                    {value_series} AS value_series,
                    data_type AS DataType,
                    (SELECT description FROM experimental_design_type WHERE agg.experimental_design_type_id = experimental_design_type.id) AS ExperimentalDesignType,
                    (SELECT description FROM response_variable_type WHERE agg.response_variable_type_id = response_variable_type.id) AS ResponseVariableType
                FROM
                    {aggregated_table} agg
                    INNER JOIN taxon ON taxon.id = taxon_id
                    INNER JOIN search_type ON search_type.id = search_type_id
                    INNER JOIN source ON source.id = source_id
                    INNER JOIN unit ON unit.id = unit_id
                    LEFT JOIN region ON region.id = region_id
                WHERE taxon_id = :taxon_id
                AND start_date_y >= :min_year
                AND start_date_y <= :max_year
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
                        aggregated_table = aggregated_table
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
                data['ID'] = i
                i += 1

                # This is going to get calculated downstream anyway:

                # if len(year_data) > 0:
                    # years = [int(year) for year in year_data.keys()]
                    # data['TimeSeriesLength'] = max(years) - min(years) + 1
                    # data['TimeSeriesCompleteness'] = "%0.3f" % (float(len(years)) / (max(years) - min(years) + 1))

                # Remove unwanted key from dict
                del data['value_series']

                writer.writerow(data)

    log.info("Done")

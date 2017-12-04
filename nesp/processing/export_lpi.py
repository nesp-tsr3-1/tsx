from nesp.db import get_session
from tqdm import tqdm
import logging
from nesp.util import run_parallel
import time
import csv
import os
import nesp.config

log = logging.getLogger(__name__)

def process_database(species = None):
    session = get_session()

    if species == None:
        taxa = [taxon_id for (taxon_id,) in session.execute("SELECT DISTINCT taxon_id FROM aggregated_by_year").fetchall()]
    else:
        taxa = [taxon_id for (taxon_id,) in session.execute(
            "SELECT DISTINCT taxon_id FROM t2_processed_sighting, taxon WHERE taxon.id = taxon_id AND spno IN :species", {
                'species': species
            }).fetchall()]

    # Get year range
    min_year, max_year = session.execute("""SELECT MIN(start_date_y), MAX(start_date_y) FROM t2_processed_survey""").fetchone()

    # Without this, the GROUP_CONCAT in the export query produces rows that are too long
    session.execute("""SET SESSION group_concat_max_len = 4096;""")

    export_dir = nesp.config.data_dir('export')
    filename = 'lpi.csv'

    with open(os.path.join(export_dir, filename), 'w') as csvfile:
        fieldnames = [
            'SpNo',
            'TaxonID',
            'CommonName',
            'SiteDesc',
            'SourceDesc',
            'SubIBRA',
            'Unit',
            'SearchTypeDesc',
            'TimeSeriesLength',
            'TimeSeriesCompleteness',
            'SpatialAccuracy',
            'TaxonSpatialRepresentativeness'
        ] + [str(year) for year in range(min_year, max_year + 1)]

        writer = writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        for taxon_id in tqdm(taxa):
            result = session.execute("""SELECT
                    taxon.spno AS SpNo,
                    taxon.id AS TaxonID,
                    taxon.common_name AS CommonName,
                    search_type.description AS SearchTypeDesc,
                    COALESCE(
                        CONCAT('site_', site_id),
                        CONCAT('grid_', grid_cell_id)) AS SiteDesc,
                    NULL AS SourceDesc, # TODO
                    NULL AS SubIBRA, # TODO
                    NULL AS Unit, # TODO: based on response variable type
                    GROUP_CONCAT(CONCAT(start_date_y, '=', value) ORDER BY start_date_y) AS value_by_year
                FROM
                    aggregated_by_year
                    INNER JOIN taxon ON taxon.id = taxon_id
                    INNER JOIN search_type ON search_type.id = search_type_id
                WHERE taxon_id = :taxon_id
                AND data_type = 2
                GROUP BY
                    source_id,
                    search_type_id,
                    COALESCE(site_id, grid_cell_id),
                    experimental_design_type_id,
                    response_variable_type_id
                    """,
                    {
                        'taxon_id': taxon_id
                    })

            keys = result.keys()

            for row in tqdm(result.fetchall()):
                # Get row as a dict
                data = dict(zip(keys, row))

                # Parse out the yearly values
                year_data = dict(item.split('=') for item in data['value_by_year'].split(','))

                # Populate years in output
                data.update(year_data)
                if len(year_data) > 0:
                    years = [int(year) for year in year_data.keys()]
                    data['TimeSeriesLength'] = max(years) - min(years) + 1
                    data['TimeSeriesCompleteness'] = "%0.3f" % (float(len(years)) / (max(years) - min(years) + 1))

                # Remove unwanted key from dict
                del data['value_by_year']

                writer.writerow(data)

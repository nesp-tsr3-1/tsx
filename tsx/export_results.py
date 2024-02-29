from tsx.db import get_session
import sqlite3
import logging
import pandas as pd
from collections import defaultdict
import sys
import argparse
import re
import os
from sqlalchemy import text

log = logging.getLogger(__name__)

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser(description='Exports results of workflow into a single SQLite file for archival')
    parser.add_argument('lpi_wide', type=str, help='LPI wide table with final results filtered-lpi.csv')
    # parser.add_argument('trend_dir', type=str, help='Directory containing permutation trends')
    parser.add_argument('output_db', type=str, help='SQLite file to save results in')

    args = parser.parse_args()

    db = sqlite3.connect(args.output_db)
    export_lpi_wide(db, args.lpi_wide)
    export_taxa(db)
    # export_trends(db, args.trend_dir)

def export_lpi_wide(db, lpi_wide_filename):
    dt = defaultdict(lambda: str)
    dt.update({
        'ID': int,
        'RegionCentroidLatitude': float,
        'RegionCentroidLongitude': float,
        'RegionCentroidAccuracy':float,
        'SiteID': int,
        'SourceID': int,
        'UnitID': int,
        'DataType': int,
        'TimeSeriesLength': int,
        'TimeSeriesSampleYears': int,
        'TimeSeriesCompleteness': float,
        'TimeSeriesSamplingEvenness': float,
        'SpatialRepresentativeness': float,
        'SurveysCentroidLatitude': float,
        'SurveysCentroidLongitude': float,
        'SurveyCount': int,
        'NationalPriorityTaxa': int
    })

    df = pd.read_csv(lpi_wide_filename, index_col='ID', dtype=dt)

    # Make year columns of type float
    df = df.astype({ k: float if k.isnumeric() else v for (k,v) in df.dtypes.to_dict().items()})

    df.to_sql('time_series', db, if_exists='replace')

def export_taxa(db):
    session = get_session()

    df = pd.read_sql(text("""SELECT
        id AS TaxonID,
        taxonomic_group AS TaxonomicGroup,
        common_name AS CommonName,
        scientific_name AS ScientificName,
        (SELECT
            GROUP_CONCAT(
                CONCAT(taxon_group.group_name, COALESCE(CONCAT(':', taxon_group.subgroup_name), ''))
            )
            FROM taxon_group
            WHERE taxon_group.taxon_id = taxon.id
        ) AS FunctionalGroup,
        taxon.national_priority AS NationalPriorityTaxa,
        (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.epbc_status_id) AS EPBCStatus,
        (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.iucn_status_id) AS IUCNStatus,
        (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.state_status_id) AS StatePlantStatus,
        (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.bird_action_plan_status_id) AS BirdActionPlanStatus,
        (SELECT description FROM taxon_status WHERE taxon_status.id = taxon.max_status_id) AS MaxStatus
        FROM taxon"""), session.connection())
    df.to_sql('taxon', db, if_exists='replace')

def export_trends(db, trend_dir):
    rows = get_trends(trend_dir)
    df = pd.DataFrame(rows, dtype=str)
    df.rename(columns={
        'tgroup': 'TaxonomicGroup',
        'group': 'FunctionalGroup',
        'subgroup': 'FunctionalSubGroup',
        'priority': 'NationalPriorityTaxa',
        'ref_year': 'ReferenceYear',
        'state': 'State',
        'statusauth': 'StatusAuthority',
        'status': 'Status',
        'management': 'Management',
        'trend_data': 'TrendData'
    }, inplace=True)
    # Reorder columns
    df = df[[
        'TaxonomicGroup',
        'FunctionalGroup',
        'FunctionalSubGroup',
        'NationalPriorityTaxa',
        'ReferenceYear',
        'State',
        'StatusAuthority',
        'Status',
        'Management',
        'TrendData'
    ]]
    df = df.fillna('')
    # df['State'] = df['State'].map(abbreviate)
    df['Status'] = df['Status'].map(abbreviate)
    df['Status'] = df['Status'].str.replace("+", "_", regex=False)

    for col in ['TaxonomicGroup', 'FunctionalGroup', 'FunctionalSubGroup', 'State', 'Management']:
        df[col] = df[col].replace('', 'All')

    df = df.astype({ 'ReferenceYear': int })
    df.to_sql('trend', db, if_exists='replace', index=False)

def abbreviate(x):
    subs = [
        ("Near Threatened", "NT"),
        ("Critically Endangered", "CR"),
        ("Vulnerable", "VU"),
        ("Endangered", "EN"),
        ("Victoria", "VIC"),
        ("South Australia", "SA"),
        ("Western Australia", "WA"),
        ("New South Wales", "NSW"),
        ("Australian Capital Territory", "ACT"),
        ("Northern Territory", "NT"),
        ("Queensland", "QLD"),
        ("Tasmania", "TAS"),
        (">", "gt-"),
        ("<", "lt-")
    ]
    for old, new in subs:
        x = x.replace(old, new)
    return x

def get_trends(trend_dir):
    rows = []
    for root, dirs, files in os.walk(trend_dir):
        path = os.path.relpath(root, trend_dir)
        if "_" not in path:
            continue
        info = dict(part.split("-", 1) for part in path.strip("_").split("_"))
        for file in files:
            match = re.match(r"nesp_(\d+)_infile_Results.txt", file)
            if match:
                info['ref_year'] = match[1]
                with open(os.path.join(root, file)) as file:
                    info['trend_data'] = file.read()
                rows.append(dict(info))
    return rows


if __name__ == '__main__':
    main()

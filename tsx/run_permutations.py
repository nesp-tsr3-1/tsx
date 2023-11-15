import sqlite3
import logging
import pandas as pd
from collections import defaultdict, namedtuple
import sys
import argparse
import re
import os
from tsx.util import run_parallel
from tempfile import TemporaryDirectory
import importlib.resources
import subprocess
from tqdm import tqdm
import shutil
from tsx.api.results import get_dotplot_data, get_summary_data, get_intensity_data
from random import shuffle

log = logging.getLogger(__name__)

reference_years = [1985, 1990, 1995, 2000]
end_year = 2019
generate_plot_data = True

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser(description='Run trend permutations')
    parser.add_argument('lpi_wide', type=str, help='LPI wide table with final results (lpi-filtered.csv)')
    parser.add_argument('output_db', type=str, help='SQLite file to save results in')

    args = parser.parse_args()

    db = sqlite3.connect(args.output_db)
    df = load_lpi_wide(args.lpi_wide)

    run_permutations(db, df)

def iterate_partitions(df, column, except_for=[]):
    if 'All' not in except_for:
        yield ('All', df)
    for value in df[column].drop_duplicates():
        if value not in except_for:
            yield (value, df[df[column] == value])

def iterate_states(df):
    yield from iterate_partitions(df, 'State', except_for=['Commonwealth'])
    yield ('Australian Capital Territory+New South Wales', df[(df['State'] == 'Australian Capital Territory') | (df['State'] == 'New South Wales')])

def iterate_groups(df, tgroup):
    group_series = df['FunctionalGroup'].str.split(",")

    if tgroup == 'All':
        # Only include groups that cross more than one TaxonomicGroup
        d = df[['TaxonomicGroup','FunctionalGroup']].drop_duplicates()
        d['FunctionalGroup'] = d['FunctionalGroup'].str.replace(':[^,]*', '', regex=True).str.split(',')
        d = d.explode('FunctionalGroup').drop_duplicates()
        d = d.groupby('FunctionalGroup').agg({'TaxonomicGroup': 'nunique'})
        groups = d[d['TaxonomicGroup'] > 1].index
    else:
        groups = (group_series.drop_duplicates().explode().drop_duplicates().str.split(":", n=1, expand=True)[0].drop_duplicates().dropna())

    yield ('All', df)
    for group in groups:
        yield (group, df[group_series.apply(lambda x: any(y.split(":")[0] == group for y in x))])

def iterate_subgroups(df, tgroup, group):
    yield ('All', df)
    # Only include subgroups if both TaxonomicGroup and FunctionalGroup are selected
    if group != "All" and tgroup != "All":
        groups = df['FunctionalGroup'].drop_duplicates().str.split(",").explode().drop_duplicates()
        subgroups = [g.split(":")[1] for g in groups if g.startswith(group + ":")]

        for subgroup in subgroups:
            g = group + ':' + subgroup
            yield (subgroup, df[df['FunctionalGroup'].apply(lambda x: g in x)])

def abbreviate_status(status):
    return {
        "Near Threatened": "NT",
        "Critically Endangered": "CR",
        "Vulnerable": "VU",
        "Endangered": "EN",
        "Least Concern": "LC"
    }.get(status, "??")

def iterate_status(df):
    for status_authority in ['Max', 'IUCN', 'EPBC', 'BirdActionPlan']:
        status_col = df[status_authority + 'Status']
        status_abbr = status_col.apply(abbreviate_status)
        for status in ['NT_VU_EN_CR', 'VU_EN_CR', 'NT']:
            new_df = df[status_abbr.apply(lambda x: x in status)]
            if len(new_df):
                yield (status_authority, status, new_df)

def iterate_permutations(df):
    for taxon_id, _df in iterate_partitions(df, 'TaxonID', except_for=['All']):
        yield ({ 'TaxonID': taxon_id }, _df)

    for tgroup, df in iterate_partitions(df, 'TaxonomicGroup'):
        for group, df in iterate_groups(df, tgroup):
            for state, df in iterate_states(df):
                for management, df in iterate_partitions(df, 'Management'):
                    yield ({
                      'State': state,
                      'TaxonomicGroup': tgroup,
                      'Management': management,
                      'FunctionalGroup': group,
                      'NationalPriorityTaxa': 1
                    }, df[df['NationalPriorityTaxa'] == 1])
                    for subgroup, df in iterate_subgroups(df, tgroup, group):
                        for status_authority, status, df in iterate_status(df):
                            yield ({
                                'State': state,
                                'TaxonomicGroup': tgroup,
                                'Management': management,
                                'FunctionalGroup': group,
                                'FunctionalSubGroup': subgroup,
                                'StatusAuthority': status_authority,
                                'Status': status
                            }, df)

def abbreviate(x):
    subs = [
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

def sanitise_filename(name):
    return re.sub(r"[/\\:$?*\"]", "_", name)

def permutation_dir(perm):
    path = os.path.join(*[sanitise_filename("%s=%s" % (k, v)) for k, v in perm.items()])
    path = abbreviate(path)
    return path

def iterate_tasks(df, work_path, script_path):
    for perm, df in iterate_permutations(df):

        # Check if any data present
        if len(df) == 0:
            continue

        if 'TaxonID' in perm:
            path = os.path.join(work_path, permutation_dir(perm))
            os.makedirs(path, exist_ok=True)

            min_year = str(df['MinYear'].min())
            max_year = str(df['MaxYear'].max())
            drop_cols = [col for col in list(df.columns) if col.isnumeric() and (col < min_year or col > max_year)]
            df = df.drop(columns = drop_cols)

            df.to_csv(os.path.join(path, 'input.csv'))
            yield perm, path, script_path
        else:
            for year in reference_years:
                perm = dict(perm)
                perm['ReferenceYear'] = year

                if df[(df['MinYear'] <= year) & (df['MaxYear'] >= year)]['TaxonID'].nunique() < 3:
                    yield perm, None, None
                    continue

                path = os.path.join(work_path, permutation_dir(perm))
                os.makedirs(path, exist_ok=True)
                df.to_csv(os.path.join(path, 'input.csv'))

                yield perm, path, script_path

def run_task(perm, work_path, script_path):
    if work_path is None:
        return (perm, None)

    result_file = os.path.join(work_path, "data_infile_Results.txt")
    if not os.path.exists(result_file):
        with open(os.path.join(work_path, "stdout.txt"), "wb") as stdout:
            with open(os.path.join(work_path, "stderr.txt"), "wb") as stderr:
                if 'ReferenceYear' in perm:
                    subprocess.run(["Rscript", script_path, os.path.join(work_path, "input.csv"), work_path, str(perm['ReferenceYear']), str(end_year)], stdout=stdout, stderr=stderr)
                else:
                    subprocess.run(["Rscript", script_path, os.path.join(work_path, "input.csv"), work_path], stdout=stdout, stderr=stderr)
    with open(result_file) as f:
        trend_data = f.read()
    # Clean up extraneous files
    for file in os.listdir(work_path):
        if file not in ["data_infile_Results.txt", "stdout.txt", "stderr.txt", "input.csv"]:
            remove_file_or_dir(os.path.join(work_path, file))

    if generate_plot_data:
        df = load_lpi_wide(os.path.join(work_path, "input.csv"))
        with open(os.path.join(work_path, "dotplot.csv"), "w") as f:
            f.write(get_dotplot_data(df, format='csv'))
        with open(os.path.join(work_path, "summary-plot.csv"), "w") as f:
            f.write(get_summary_data(df, format='csv'))
        with open(os.path.join(work_path, "map.csv"), "w") as f:
            f.write(get_intensity_data(df, format='csv'))

    return (perm, trend_data)

def remove_file_or_dir(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def run_permutations(db, df):
    db.execute("""DROP TABLE IF EXISTS trend""");
    db.execute("""CREATE TABLE trend (
        TaxonomicGroup TEXT,
        FunctionalGroup TEXT,
        FunctionalSubGroup TEXT,
        NationalPriorityTaxa TEXT,
        ReferenceYear INTEGER,
        State TEXT,
        StatusAuthority TEXT,
        Status TEXT,
        Management TEXT,
        TaxonID TEXT,
        TrendData BLOB
    );""")

    # with TemporaryDirectory() as work_path:
    work_path='/tmp/tsxperm'
    script_path = os.path.join(work_path, "lpi.R")
    # Write LPI script into temp dir
    with open(script_path, "wb") as f:
        f.write(importlib.resources.read_binary("tsx.resources", "lpi.R"))

    # This first generates all tasks (takes a few minutes), so that we can show a meaningful progress indicator for the next phase
    tasks = list(tqdm(iterate_tasks(df, work_path, script_path)))
    # Randomise tasks to get a more consistent progress rate
    shuffle(tasks)

    for result, error in run_parallel(run_task, tqdm(tasks)):
        if result:
            perm, trend = result
            perm['TrendData'] = trend
            sql = "INSERT INTO trend (%s) VALUES (%s)" % (", ".join(perm.keys()), ", ".join(":" + k for k in perm.keys()))
            db.execute(sql, perm)
            db.commit()

def load_lpi_wide(lpi_wide_filename):
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
    # Calculate min/max year for each time series
    df[['MinYear','MaxYear']] = (df[(c for c in df.columns if c.isnumeric())]
                .melt(ignore_index=False)
                .pipe(lambda x: x[x.value.notna()])['variable']
                .groupby('ID')
                .agg(['min', 'max'])
                .astype(int))
    return df

if __name__ == '__main__':
    main()

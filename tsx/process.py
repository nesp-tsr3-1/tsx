import argparse
import shapely.geometry
import shapely.wkb
import tsx.config
from tqdm import tqdm
import logging
import os
from tsx.db import get_session
from tsx.mysql_to_sqlite import export_to_sqlite
import binascii
from tsx.util import get_resource
import subprocess
import shutil
from datetime import datetime
import random
import tsx.processing.alpha_hull
import tsx.processing.t1_aggregation
import tsx.processing.t2_aggregation
import tsx.processing.export_lpi
import tsx.processing.spatial_rep
import tsx.processing.filter_time_series
import fiona
from tsx.geo import to_multipolygon
from sqlalchemy import text

log = logging.getLogger(__name__)

# Helper to make logging and progress bar work together
class TqdmStream(object):
    def write(self, x):
        tqdm.write(x.strip())
    def flush(self):
        pass

def main():
    logging.basicConfig(stream=TqdmStream(), level=logging.INFO, format='%(asctime)-15s %(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser(description='TSX processing utility')

    parser.add_argument('--species', '-s', help='Comma separated list of species numbers (SPNO) to process')
    parser.add_argument('--commit', '-c', action='store_true', dest='commit', help='Commit changes to database (default is dry-run)')

    subparsers = parser.add_subparsers(help = 'command', dest = 'command')

    p = subparsers.add_parser('alpha_hull')
    p = subparsers.add_parser('export')

    p.add_argument('layers', nargs='+', choices=['alpha', 'ultrataxa', 'pa'], help='Layers to export')

    p = subparsers.add_parser('range_ultrataxon') # LEGACY
    p = subparsers.add_parser('pseudo_absence') # LEGACY
    p = subparsers.add_parser('t1_aggregation')
    p = subparsers.add_parser('t2_aggregation')
    p = subparsers.add_parser('response_variable') # LEGACY
    p = subparsers.add_parser('export_lpi')

    p.add_argument('--monthly', '-m', action='store_true', dest='monthly', help='Output a column for each month')
    p.add_argument('--filter', '-f', action='store_true', dest='filter', help='Filter output')
    p.add_argument('--all-years', '-a', action='store_true', dest='include_all_years_data', help='Include data for all years')

    p = subparsers.add_parser('spatial_rep')
    p = subparsers.add_parser('filter_time_series')
    p = subparsers.add_parser('clear')
    p = subparsers.add_parser('all')
    p = subparsers.add_parser('simple')

    p = subparsers.add_parser('single_source')
    p.add_argument('source_id', type=int, help='Source ID to process')
    p.add_argument('--output-dir', '-o', help='Output directory for processed data')

    args = parser.parse_args()

    species = None
    try:
        if args.species:
            species = [int(spno) for spno in args.species.split(",")]
    except ValueError:
        parser.error('--species argument must be a comma-separated list of integers')

    if args.commit != True:
        log.info("Not committing any changes to database (dry-run only)")

    if args.command == 'alpha_hull':
        tsx.processing.alpha_hull.process_database(species = species, commit = args.commit)
    elif args.command == 'export':
        export(args.layers, species = species)
    elif args.command == 't1_aggregation':
        tsx.processing.t1_aggregation.process_database(species = species, commit = args.commit)
    elif args.command == 't2_aggregation':
        tsx.processing.t2_aggregation.process_database(species = species, commit = args.commit)
    elif args.command == 'export_lpi':
        tsx.processing.export_lpi.process_database(species = species, monthly = args.monthly, filter_output = args.filter, include_all_years_data = args.include_all_years_data)
    elif args.command == 'spatial_rep':
        tsx.processing.spatial_rep.process_database(species = species, commit = args.commit)
    elif args.command == 'filter_time_series':
        if not args.commit:
            log.error("Dry-run mode not supported for 'filter_time_series'")
            return
        if args.species:
            log.error("Passing species not supported for 'filter_time_series'")
            return
        tsx.processing.filter_time_series.process_database()
    elif args.command == 'clear':
        if not args.commit:
            log.error("Dry-run mode not supported for 'clear'")
            return
        clear_database()
    elif args.command == 'all':
        if not args.commit:
            log.error("Dry-run mode not supported for 'all'")
            return
        if args.species:
            log.error("Passing species not supported for 'all'")
            return

        log.info("STEP 0 - CLEARING PREVIOUS RESULTS")
        clear_database()

        log.info("STEP 1 - ALPHA HULLS")
        tsx.processing.alpha_hull.process_database(commit = True)

        log.info("STEP 2 - TYPE 1 DATA AGGREGATION")
        tsx.processing.t1_aggregation.process_database(commit = True)

        log.info("STEP 3 - TYPE 2 DATA AGGREGATION")
        tsx.processing.t2_aggregation.process_database(commit = True)

        log.info("STEP 4 - CALCULATE SPATIAL REPRESENTATIVENESS")
        tsx.processing.spatial_rep.process_database(commit = True)

        log.info("STEP 5 - FILTER TIME SERIES")
        tsx.processing.filter_time_series.process_database()

        log.info("PROCESSING COMPLETE")

    elif args.command == 'simple':
        if not args.commit:
            log.error("Dry-run mode not supported for 'simple'")
            return
        if args.species:
            log.error("Passing species not supported for 'simple'")
            return

        log.info("STEP 0 - CLEARING PREVIOUS RESULTS")
        clear_database()

        log.info("STEP 1 - TYPE 1 DATA AGGREGATION")
        tsx.processing.t1_aggregation.process_database(commit = True, simple_mode = True)

        log.info("STEP 2 - EXPORT")
        tsx.processing.export_lpi.process_database()

        log.info("PROCESSING COMPLETE")

    elif args.command == 'single_source':
        log.info("Processing source %s" % args.source_id)
        process_source(args.source_id, args.output_dir)

tmp_dir = '/tmp/tsx-work'

def is_csv_empty(path):
    with open(path, 'r') as f:
        for count, line in enumerate(f):
            if count > 1:
                return False

    return True

def process_source(source_id, output_dir = None):
    dt = datetime.now()
    path = os.path.join(tmp_dir, str(dt.date()), str(dt.time()) + '-' + random.randbytes(3).hex())
    log.info("Work directory: %s" % path)
    sqlite_db = os.path.join(path, 'data.sqlite')
    os.makedirs(path, exist_ok = True)
    log.info("Exporting to sqlite")
    export_to_sqlite(source_id, sqlite_db)
    database_url = 'sqlite:///' + sqlite_db
    log.info("Performing t1_aggregation")
    tsx.processing.t1_aggregation.process_database(commit = True, simple_mode = True, database_config = database_url)
    log.info("Performing export_lpi")
    tsx.processing.export_lpi.process_database(database_config = database_url, export_dir = path)

    if is_csv_empty(os.path.join(path, 'lpi.csv')):
        log.info('No data to process')
        # Creating the output dir indicates that processing is complete
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        return

    log.info("Running LPI analysis")
    with open(os.path.join(path, "lpi.R"), "wb") as f:
        f.write(get_resource("lpi.R").read_bytes())
    subprocess.run(["Rscript", os.path.join(path, "lpi.R"), os.path.join(path, "lpi.csv"), path])
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy(os.path.join(path, "lpi.csv"), os.path.join(output_dir, "aggregated.csv"))
        shutil.copy(os.path.join(path, "data_infile_Results.txt"), os.path.join(output_dir, "trend.csv"))
    log.info("done")

def clear_database():
    # Clears out all derived data from the database
    session = get_session()
    statements = [
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE taxon_presence_alpha_hull;",
        "TRUNCATE taxon_presence_alpha_hull_subdiv;",
        "TRUNCATE t2_survey_site;",
        "TRUNCATE aggregated_by_year;",
        "TRUNCATE aggregated_by_month;",
        "SET FOREIGN_KEY_CHECKS = 1;"
    ]

    for sql in tqdm(statements):
        session.execute(text(sql))

    session.commit()


# ----- Export shapefiles showing processed data

def export(layers, species = None):
    session = get_session()

    export_alpha = 'alpha' in layers

    export_dir = tsx.config.data_dir('export')

    if species == None:
        species = get_all_spno(session)

    for spno in tqdm(species):
        if export_alpha:
            filename = os.path.join(export_dir, '%s-alpha.shp' % spno)

            alpha_hulls = session.execute(text("""SELECT taxon_id, range_id, breeding_range_id, HEX(ST_AsWKB(geometry))
                    FROM taxon_presence_alpha_hull, taxon
                    WHERE taxon_id = taxon.id
                    AND spno = :spno"""), {
                        'spno': spno
                    }).fetchall()

            if len(alpha_hulls) > 0:

                with fiona.open(filename, 'w',
                    driver='ESRI Shapefile',
                    crs={'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'},
                    schema={
                        'geometry': 'MultiPolygon',
                        'properties': {
                            'TAXONID': 'str',
                            'RNGE': 'int',
                            'BRRNGE': 'int'
                        }
                    }) as output:

                    for taxon_id, range_id, breeding_range_id, geom_wkb in alpha_hulls:
                        geom = to_multipolygon(shapely.wkb.loads(binascii.unhexlify(geom_wkb)))

                        if len(geom) == 0:
                            continue

                        output.write({
                            'geometry': shapely.geometry.mapping(geom),
                            'properties': {
                                'TAXONID': taxon_id,
                                'RNGE': range_id,
                                'BRRNGE': breeding_range_id
                            }
                        })

def get_all_spno(session):
    return [spno for (spno,) in session.execute(text("SELECT DISTINCT spno FROM taxon")).fetchall()]

if __name__ == '__main__':
    main()

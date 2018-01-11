import argparse
import tempfile
import shapely.geometry
import shapely.wkb
import nesp.config
import nesp.processing.alpha_hull
import nesp.processing.range_ultrataxon
import nesp.processing.pseudo_absence
import nesp.processing.t1_aggregation
import nesp.processing.response_variable
import nesp.processing.export_lpi
import nesp.processing.spatial_rep
import fiona
from tqdm import tqdm
import logging
import os
from nesp.geo import to_multipolygon
from nesp.db import get_session
from shapely.geometry import Point

log = logging.getLogger(__name__)

# Helper to make logging and progress bar work together
class TqdmStream(object):
    def write(self, x):
        tqdm.write(x.strip())
    def flush(self):
        pass

def main():
    logging.basicConfig(stream=TqdmStream(), level=logging.INFO, format='%(asctime)-15s %(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser(description='NESP processing utility')

    parser.add_argument('--species', '-s', help='Comma separated list of species numbers (SPNO) to process')
    parser.add_argument('--commit', '-c', action='store_true', dest='commit', help='Commit changes to database (default is dry-run)')

    subparsers = parser.add_subparsers(help = 'command', dest = 'command')

    p = subparsers.add_parser('alpha_hull')
    p = subparsers.add_parser('export')

    p.add_argument('layers', nargs='+', choices=['alpha', 'ultrataxa', 'pa', 'grid'], help='Layers to export')

    p = subparsers.add_parser('range_ultrataxon')
    p = subparsers.add_parser('pseudo_absence')
    p = subparsers.add_parser('t1_aggregation')
    p = subparsers.add_parser('response_variable')
    p = subparsers.add_parser('export_lpi')

    p.add_argument('--monthly', '-m', action='store_true', dest='monthly', help='Output a column for each month')
    p.add_argument('--filter', '-f', action='store_true', dest='filter', help='Filter output')

    p = subparsers.add_parser('spatial_rep')
    p = subparsers.add_parser('all')
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
        nesp.processing.alpha_hull.process_database(species = species, commit = args.commit)
    elif args.command == 'export':
        export(args.layers, species = species)
    elif args.command == 'range_ultrataxon':
        nesp.processing.range_ultrataxon.process_database(species = species, commit = args.commit)
    elif args.command == 'pseudo_absence':
        nesp.processing.pseudo_absence.process_database(commit = args.commit)
    elif args.command == 't1_aggregation':
        nesp.processing.t1_aggregation.process_database(species = species, commit = args.commit)
    elif args.command == 'response_variable':
        nesp.processing.response_variable.process_database(species = species, commit = args.commit)
    elif args.command == 'export_lpi':
        nesp.processing.export_lpi.process_database(species = species, monthly = args.monthly, filter_output = args.filter)
    elif args.command == 'spatial_rep':
        nesp.processing.spatial_rep.process_database(species = species, commit = args.commit)
    elif args.command == 'all':
        if not args.commit:
            log.error("Dry-run mode not supported for 'all'")
            return
        if args.species:
            log.error("Passing species not supported for 'all'")
            return

        log.info("STEP 1 - ALPHA HULLS")
        nesp.processing.alpha_hull.process_database(commit = True)

        log.info("STEP 2 - RANGE AND ULTRATAXON DEFINITION")
        nesp.processing.range_ultrataxon.process_database(commit = True)

        log.info("STEP 3 - GENERATE PSEUDO ABSENCES")
        nesp.processing.pseudo_absence.process_database(commit = True)

        log.info("PROCESSING COMPLETE")

# ----- Export shapefiles showing processed data

def export(layers, species = None):
    session = get_session()

    export_alpha = 'alpha' in layers
    export_ultrataxa = 'ultrataxa' in layers
    export_pseudo_absence = 'pa' in layers
    export_grid = 'grid' in layers

    export_dir = nesp.config.data_dir('export')

    if species == None:
        species = get_all_spno(session)

    for spno in tqdm(species):
        if export_alpha:
            filename = os.path.join(export_dir, '%s-alpha.shp' % spno)

            alpha_hulls = session.execute("""SELECT taxon_id, range_id, breeding_range_id, ST_AsWKB(geometry)
                    FROM taxon_presence_alpha_hull, taxon
                    WHERE taxon_id = taxon.id
                    AND spno = :spno""", {
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
                        geom = to_multipolygon(shapely.wkb.loads(geom_wkb))

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

        if export_ultrataxa:
            filename = os.path.join(export_dir, '%s-ultrataxa.shp' % spno)

            items = session.execute("""SELECT ST_X(coords) AS x, ST_Y(coords) AS y, taxon.id, range_id, generated_subspecies, t2_survey_site.site_id, t2_survey.search_type_id
                FROM t2_ultrataxon_sighting, t2_sighting, taxon, t2_survey
                LEFT JOIN t2_survey_site ON t2_survey_site.survey_id = t2_survey.id
                WHERE t2_ultrataxon_sighting.sighting_id = t2_sighting.id
                AND t2_sighting.survey_id = t2_survey.id
                AND t2_ultrataxon_sighting.taxon_id = taxon.id
                AND taxon.spno = :spno
                """, {
                    'spno': spno
                }).fetchall()

            with fiona.open(filename, 'w',
                    driver='ESRI Shapefile',
                    crs={'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'},
                    schema={
                        'geometry': 'Point',
                        'properties': {
                            'TaxonID': 'str',
                            'Rnge': 'int',
                            'Generated': 'int',
                            'SearchType': 'int',
                            'SiteID': 'int'
                        }
                    }) as output:

                    for x, y, taxon_id, range_id, generated_subspecies, site_id, search_type_id in items:
                        geom = Point(x, y)

                        output.write({
                            'geometry': shapely.geometry.mapping(geom),
                            'properties': {
                                'TaxonID': taxon_id,
                                'Rnge': range_id,
                                'Generated': generated_subspecies,
                                'SearchType': search_type_id,
                                'SiteID': site_id
                            }
                        })

        if export_pseudo_absence:
            filename = os.path.join(export_dir, '%s-pa.shp' % spno)

            items = session.execute("""SELECT ST_X(coords) AS x, ST_Y(coords) AS y, taxon.id
                FROM t2_processed_sighting, t2_processed_survey, t2_survey, taxon
                WHERE t2_processed_sighting.survey_id = t2_processed_survey.id
                AND t2_processed_survey.raw_survey_id = t2_survey.id
                AND t2_processed_sighting.taxon_id = taxon.id
                AND taxon.spno = :spno
                AND pseudo_absence
                AND experimental_design_type_id = 1
                """, {
                    'spno': spno
                }).fetchall()

            with fiona.open(filename, 'w',
                    driver='ESRI Shapefile',
                    crs={'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'},
                    schema={
                        'geometry': 'Point',
                        'properties': {
                            'TaxonID': 'str'
                        }
                    }) as output:

                    for x, y, taxon_id in items:
                        geom = Point(x, y)

                        output.write({
                            'geometry': shapely.geometry.mapping(geom),
                            'properties': {
                                'TaxonID': taxon_id
                            }
                        })

        if export_grid:
            filename = os.path.join(export_dir, '%s-grid.shp' % spno)

            items = session.execute("""SELECT ST_X(coords) AS x, ST_Y(coords) AS y, grid_cell_id, taxon.id, pseudo_absence
                FROM t2_processed_sighting, t2_processed_survey, t2_survey, taxon
                WHERE t2_processed_sighting.survey_id = t2_processed_survey.id
                AND t2_processed_survey.raw_survey_id = t2_survey.id
                AND t2_processed_sighting.taxon_id = taxon.id
                AND taxon.spno = :spno
                AND experimental_design_type_id = 2
                """, {
                    'spno': spno
                }).fetchall()

            with fiona.open(filename, 'w',
                    driver='ESRI Shapefile',
                    crs={'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'},
                    schema={
                        'geometry': 'Point',
                        'properties': {
                            'TaxonID': 'str',
                            'GridID': 'int',
                            'Pseudo': 'int'
                        }
                    }) as output:

                    for x, y, grid_cell_id, taxon_id, pseudo_absence in items:
                        geom = Point(x, y)

                        output.write({
                            'geometry': shapely.geometry.mapping(geom),
                            'properties': {
                                'TaxonID': taxon_id,
                                'GridID': grid_cell_id,
                                'Pseudo': pseudo_absence
                            }
                        })

def get_all_spno(session):
    return [spno for (spno,) in session.execute("SELECT DISTINCT spno FROM taxon").fetchall()]

if __name__ == '__main__':
    main()

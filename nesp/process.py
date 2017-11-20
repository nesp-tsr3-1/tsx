import argparse
import tempfile
from nesp.db import get_session, Taxon, T2ProcessedSighting
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection, LineString, LinearRing, shape
from shapely.ops import transform
import shapely.wkb
import nesp.config
import nesp.processing.alpha_hull
import nesp.processing.range_ultrataxon
import fiona
import pyproj
from functools import partial
from threading import Thread, Lock
from Queue import Queue
from multiprocessing import cpu_count
from tqdm import tqdm
import logging
import os
from nesp.util import run_parallel
from nesp.geo import to_multipolygon, point_in_poly, subdivide_geometry

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
    p = subparsers.add_parser('export_alpha_hull')
    p = subparsers.add_parser('range_ultrataxon')

    args = parser.parse_args()

    species = None
    try:
        if args.species:
            species = [int(spno) for spno in args.species.split(",")]
    except ValueError:
        parser.error('--species argument must be a comma-separated list of integers')

    if args.command == 'alpha_hull':
        nesp.processing.alpha_hull.process_database(species = species, commit = args.commit)
    elif args.command == 'export_alpha_hull':
        export_alpha_hull()
    elif args.command == 'range_ultrataxon':
        nesp.processing.range_ultrataxon.process_database(species = species, commit = args.commit)

# ----- Export alpha hull

def export_alpha_hull():
    session = get_session()

    for spno in tqdm(get_all_spno(session)):
        filename = os.path.join(nesp.config.data_dir('spatial'), 'alpha-%s.shp' % spno)

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

if __name__ == '__main__':
    main()

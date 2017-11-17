import argparse
import tempfile
from nesp.db import get_session, Taxon, T2ProcessedSighting
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection, LineString, LinearRing, shape
from shapely.ops import transform
import shapely.wkb
import nesp.config
from nesp.processing.alpha_hull import make_alpha_hull
import fiona
import pyproj
from functools import partial
from threading import Thread, Lock
from Queue import Queue
from multiprocessing import cpu_count
from tqdm import tqdm
import logging
import os

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

    subparsers = parser.add_subparsers(help = 'command', dest = 'command')

    p = subparsers.add_parser('alpha_hull')
    p = subparsers.add_parser('export_alpha_hull')
    p = subparsers.add_parser('range_ultrataxon')

    # parser.add_argument('command', type=str, chosices=['alpha_hull', 'export_alpha_hull', 'range_ultrataxon'], help='processing step')

    args = parser.parse_args()

    if args.command == 'alpha_hull':
        alpha_hull()
    elif args.command == 'export_alpha_hull':
        export_alpha_hull()
    elif args.command == 'range_ultrataxon':
        range_and_ultrataxon_definition_parallel()

def reproject(geom, src_proj, dest_proj):
    fn = partial(pyproj.transform, src_proj, dest_proj)
    return transform(fn, geom)

def alpha_hull():
    session = get_session()

    # session.execute("CREATE TEMPORARY TABLE alpha_tmp (spno INT, geometry MULTIPOLYGON)")

    db_proj = pyproj.Proj('+init=EPSG:4326')
    working_proj = pyproj.Proj('+init=EPSG:3112') # GDA94 / Geoscience Australia Lambert - so that we can buffer in metres

    coastal_shape_filename = nesp.config.config.get("processing.alpha_hull", "coastal_shp")
    with fiona.open(coastal_shape_filename, 'r') as coastal_shape:
        # Convert from fiona dictionary to shapely geometry and reproject
        coastal_shape = reproject(shape(coastal_shape[0]['geometry']), pyproj.Proj(coastal_shape.crs), working_proj)

        # NOTE: simplifying coastal boundary makes things run 5-10X faster.. need to check whether we can do this
        # coastal_shape = coastal_shape.buffer(10000).simplify(10000) # Simplify to nearest 10 KM

        # TODO: This threading code works well but is over complicated.

        # Create a work queue containing all the species to be processed
        all_spno = get_all_spno(session)
        work_queue = Queue()
        result_queue = Queue()

        def enqueue(spno):
            work_queue.put((spno, get_species_points(session, spno), get_species_range_polygons(session, spno)))

        def worker():
            while True:
                try:
                    spno, raw_points, range_polygons = work_queue.get()

                    if len(raw_points) < 4:
                        # Not enough points to create an alpha
                        result_queue.put((spno, None))
                        continue

                    # Read points from database
                    points = [reproject(p, db_proj, working_proj) for p in raw_points]

                    # Generate alpha shape
                    alpha_shp = make_alpha_hull(
                        points = points,
                        coastal_shape = coastal_shape,
                        thinning_distance = nesp.config.config.getfloat('processing.alpha_hull', 'thinning_distance'),
                        alpha = nesp.config.config.getfloat('processing.alpha_hull', 'alpha'),
                        hullbuffer_distance = nesp.config.config.getfloat('processing.alpha_hull', 'hullbuffer_distance'),
                        isolatedbuffer_distance = nesp.config.config.getfloat('processing.alpha_hull', 'isolatedbuffer_distance'))

                    # Convert back to DB projection
                    alpha_shp = reproject(alpha_shp, working_proj, db_proj)
                    # Clean up geometry
                    alpha_shp = alpha_shp.buffer(0)

                    # Intersect with range polygons and return result
                    result = []
                    for taxon_id, range_id, breeding_range_id, geom_wkb in range_polygons:
                        geom = shapely.wkb.loads(geom_wkb).buffer(0)
                        geom = to_multipolygon(geom.intersection(alpha_shp))
                        if len(geom) > 0:
                            result.append((taxon_id, range_id, breeding_range_id, geom))

                    result_queue.put((spno, result))
                except:
                    log.exception("Exception processing alpha hull")
                    result_queue.put((None, None))

        n_threads = cpu_count()

        # Kick off as many threads as there are CPU cores
        # Even though Python has GIL, most of the work is done in libraries that can be parallelised, so this is actually a big win
        for i in range(0, n_threads):
            t = Thread(target = worker)
            t.daemon = True
            t.start()
            # Start filling up work queue
            if i < len(all_spno):
                enqueue(all_spno[i])

        # Get results and insert into DB (must be done on main thread)
        for i in tqdm(range(0, len(all_spno))):
            spno, result = result_queue.get()
            try:
                if result == None:
                    continue

                for taxon_id, range_id, breeding_range_id, geom in result:
                    session.execute("""INSERT INTO taxon_presence_alpha_hull (taxon_id, range_id, breeding_range_id, geometry)
                        VALUES (:taxon_id, :range_id, :breeding_range_id, ST_GeomFromWKB(_BINARY :geom_wkb))""", {
                            'taxon_id': taxon_id,
                            'range_id': range_id,
                            'breeding_range_id': breeding_range_id,
                            'geom_wkb': shapely.wkb.dumps(geom)
                        }
                    )
            finally:
                # Replenish work queue
                if i + n_threads < len(all_spno):
                    enqueue(all_spno[i])

    session.commit()

def get_all_spno(session):
    return [spno for (spno,) in session.execute("SELECT DISTINCT spno FROM taxon").fetchall()]

def get_species_points(session, spno):
    sql = """SELECT DISTINCT ST_X(coords), ST_Y(coords)
        FROM t2_survey, t2_sighting, taxon
        WHERE survey_id = t2_survey.id
        AND taxon_id = taxon.id
        AND spno = :spno"""

    return [Point(x,y) for x, y in session.execute(sql, { 'spno': spno }).fetchall()]

def get_species_range_polygons(session, spno):
    return session.execute("""SELECT taxon_id, range_id, breeding_range_id, ST_AsWKB(geometry)
                        FROM taxon_range, taxon
                        WHERE taxon_id = taxon.id
                        AND spno = :spno
                        """, { 'spno': spno }).fetchall()

def get_all_taxon_ids(session):
    return [id for (id,) in session.execute("SELECT taxon_id FROM taxon").fetchall()]

def get_taxon_range_polygons(session, taxon_id):
    return session.execute("""SELECT range_id, breeding_range_id, ST_AsWKB(geometry)
                        FROM taxon_range
                        WHERE taxon_id = :taxon_id
                        """, { 'taxon_id': taxon_id }).fetchall()

def to_multipolygon(geom):
    if type(geom) == MultiPolygon:
        return geom
    elif type(geom) == Polygon:
        return MultiPolygon([geom])
    elif type(geom) == GeometryCollection:
        return MultiPolygon([poly for g in geom for poly in to_multipolygon(g)])
    else:
        return MultiPolygon([])

def export_alpha_hull():
    session = get_session()

    filename = os.path.join(nesp.config.data_dir('spatial'), 'alpha-export.shp')
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

        q = session.execute("SELECT taxon_id, range_id, breeding_range_id, ST_AsWKB(geometry) FROM taxon_presence_alpha_hull")
        for taxon_id, range_id, breeding_range_id, geom_wkb in tqdm(q.fetchall()):
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

def tile_key(x, y, z):
    x = int((1 << z) * (x + 180) / 360)
    y = int((1 << z) * (y + 90) / 180)
    return (x, y, z)

def tile_bounds(key):
    x, y, z = key
    # Back to lat, lon range
    minx = float(x * 360) / (1 << z) - 180
    miny = float(y * 180) / (1 << z) - 90
    maxx = float((x + 1) * 360) / (1 << z) - 180
    maxy = float((y + 1) * 180) / (1 << z) - 90

    return Polygon.from_bounds(minx, miny, maxx, maxy)

import time

def count_points(geom):
    if geom.is_empty:
        return 0
    if type(geom) == Point:
        return 1
    if type(geom) == Polygon:
        return len(geom.exterior.coords) + sum([len(i.coords) for i in geom.interiors])
    if type(geom) in (LineString, LinearRing):
        return len(geom)
    else:
        return sum([count_points(g) for g in geom])

def point_in_poly(poly, x, y, cache, z = 4): # z = 4 chosen based on testing
    if z > 18:
       return poly.contains(Point(x, y))

    key = tile_key(x, y, z)

    if key not in cache:
        bounds = tile_bounds(key)
        start = time.time()
        intersection = poly.intersection(bounds)
        end = time.time()
        t = end - start
        if t > 1:
            tqdm.write("Slow intersection took %ss at %s" % (t, (x, y, z)))
            tqdm.write("Points: %s -> %s" % (count_points(poly), count_points(intersection)))

        if intersection.is_empty:
            cache[key] = False
        elif intersection == bounds:
            cache[key] = True
        else:
            cache[key] = intersection

    val = cache[key]

    if val == True:
        return True
    elif val == False:
        return False
    else:
        return point_in_poly(val, x, y, cache, z = z + 2) # z + 2 chosen based on testing

# TODO - put in separate module

def range_and_ultrataxon_definition_parallel():
    session = get_session()

    work_q = Queue()
    completed_q = Queue() # Just used to track progress
    lock = Lock()
    taxa = session.query(Taxon).all()

    def worker():
        while True:
            try:
                range_and_ultrataxon_definition(work_q.get())
            finally:
                completed_q.put(None)

    for taxon in taxa:
        work_q.put(taxon.id)

    for i in range(0, cpu_count()):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    # Show progress
    for taxon in tqdm(taxa):
        completed_q.get()

def range_and_ultrataxon_definition(taxon_id):
    session = get_session()

    taxon = session.query(Taxon).get(taxon_id)

    for range_id, breeding_range_id, geom_wkb in get_taxon_range_polygons(session, taxon.id):
        if not taxon.ultrataxon:
            log.warning("Unexpected range polygon for non-ultrataxon: %s" % taxon.id)
            continue

        tqdm.write("Taxon: %s, range: %s" % (taxon.id, range_id))

        cache = {}

        geom = shapely.wkb.loads(geom_wkb).buffer(0) # Ensure valid

        bounds_wkb = shapely.wkb.dumps(Polygon.from_bounds(*geom.bounds))

        # Get all sightings matching that taxon
        q = session.execute("""SELECT t2_sighting.id, ST_X(coords), ST_Y(coords)
            FROM t2_sighting, t2_survey
            WHERE t2_sighting.survey_id = t2_survey.id
            AND t2_sighting.taxon_id = :taxon_id
            AND t2_sighting.taxon_id NOT IN (SELECT taxon_id FROM t2_processed_sighting WHERE sighting_id = t2_sighting.id)
            AND MBRContains(ST_GeomFromWKB(_BINARY :bounds_wkb), coords) """, {
            'taxon_id': taxon.id,
            'bounds_wkb': bounds_wkb
        })

        records = []

        for sighting_id, x, y in q.fetchall():
            if point_in_poly(geom, x, y, cache):
                records.append(T2ProcessedSighting(
                    sighting_id = sighting_id,
                    taxon_id = taxon.id,
                    range_id = range_id,
                    generated_subspecies = False # TODO: populate this properly for Birdata sightings
                ))

        if taxon.taxon_level.description == 'ssp':
            # Get parent taxa (species) sightings
            q = session.execute("""SELECT t2_sighting.id, ST_X(coords), ST_Y(coords)
                FROM t2_sighting, t2_survey, taxon taxon_ssp, taxon taxon_sp
                WHERE t2_sighting.survey_id = t2_survey.id
                AND t2_sighting.taxon_id = taxon_sp.id
                AND taxon_ssp.id NOT IN (SELECT taxon_id FROM t2_processed_sighting WHERE sighting_id = t2_sighting.id)
                AND taxon_sp.taxon_level_id = (SELECT id FROM taxon_level WHERE description = 'sp')
                AND taxon_sp.spno = taxon_ssp.spno
                AND taxon_ssp.id = :taxon_id
                AND MBRContains(ST_GeomFromWKB(_BINARY :bounds_wkb), coords) """, {
                'taxon_id': taxon.id,
                'bounds_wkb': bounds_wkb
            })

            for sighting_id, x, y in q.fetchall():
                if point_in_poly(geom, x, y, cache):
                    records.append(T2ProcessedSighting(
                        sighting_id = sighting_id,
                        taxon_id = taxon.id,
                        range_id = range_id,
                        generated_subspecies = True
                    ))

        session.bulk_save_objects(records)
    session.commit()

if __name__ == '__main__':
    main()

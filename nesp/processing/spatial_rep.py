
import fiona
from shapely.ops import transform
from functools import partial
import pyproj
import sys, os, getopt
from shapely.geometry import shape, Point, GeometryCollection
from nesp.geo import to_multipolygon
from nesp.util import run_parallel
from nesp.db import get_session
import nesp.db.connect
import nesp.config
from tqdm import tqdm
import logging
import shapely.wkb

from nesp.db import get_session
from nesp.processing.alpha_hull import make_alpha_hull
from nesp.geo import to_multipolygon

log = logging.getLogger(__name__)

def process_database(species = None, commit = False):
    """
    Calculates spatial representativeness using alpha hulls

    Generates alpha hulls from each source x taxon combination

    Intersects alpha hulls with range layers, and then calculates percentage of range covered
    """
    session = get_session()

    if commit:
        if species == None:
            session.execute("DELETE FROM taxon_source_alpha_hull")
        else:
            session.execute("""DELETE FROM taxon_source_alpha_hull
                WHERE taxon_id IN (SELECT id FROM taxon WHERE spno IN (:species))""",
                { 'species': species })
        session.commit()

    db_proj = pyproj.Proj('+init=EPSG:4326') # Database always uses WGS84
    working_proj = pyproj.Proj('+init=EPSG:3112') # GDA94 / Geoscience Australia Lambert - so that we can buffer in metres

    # Load coastal shapefile
    coastal_shape_filename = nesp.config.config.get("processing.alpha_hull", "coastal_shp")
    with fiona.open(coastal_shape_filename, 'r') as coastal_shape:
        # Convert from fiona dictionary to shapely geometry and reproject
        coastal_shape = reproject(shape(coastal_shape[0]['geometry']), pyproj.Proj(coastal_shape.crs), working_proj)
        # Simplify coastal boundary - makes things run ~20X faster
        # log.info("Simplifying coastal boundary")
        # coastal_shape = coastal_shape.buffer(10000).simplify(10000)

    log.info("Generating alpha shapes")

    for data_type in 1,2:
        log.info("Processing type %s data" % data_type)

        # Process a single species.
        # This gets run off the main thread.
        def process(taxon_id, source_id):
            session = get_session()
            try:
                # Get raw points from DB
                raw_points = get_raw_points(session, data_type, taxon_id, source_id)

                empty = len(raw_points) < 4

                if not empty:
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

                    # Clean up geometry
                    alpha_shp = alpha_shp.buffer(0)

                    # Load core range geometry
                    core_range_geom = reproject(get_core_range_geometry(session, taxon_id), db_proj, working_proj).buffer(0)

                    # Intersect alpha hull with core range
                    intersected_geom = to_multipolygon(core_range_geom.intersection(alpha_shp))

                    # Calculate coverage
                    coverage = intersected_geom.area / core_range_geom.area

                    empty = intersected_geom.empty

                if empty:
                    session.execute("""INSERT INTO taxon_source_alpha_hull (source_id, taxon_id, data_type, core_range_coverage)
                        VALUES (:source_id, :taxon_id, :data_type, 0)""", {
                            'source_id': source_id,
                            'taxon_id': taxon_id,
                            'data_type': data_type
                        })
                else
                    session.execute("""INSERT INTO taxon_source_alpha_hull (source_id, taxon_id, data_type, geometry, core_range_coverage)
                        VALUES (:source_id, :taxon_id, :data_type, ST_GeomFromWKB(_BINARY :geom_wkb), :core_range_coverage)""", {
                            'source_id': source_id,
                            'taxon_id': taxon_id,
                            'data_type': data_type,
                            'geom_wkb': shapely.wkb.dumps(reproject(intersected_geom, working_proj, db_proj)),
                            'core_range_coverage': coverage
                        })

                if commit:
                    session.commit()

            except:
                log.exception("Exception processing alpha hull")
                raise
            finally:
                session.close()

        tasks = get_taxon_source_combinations(session, data_type, species)

        # This is important because we are about to spawn child processes, and this stops them attempting to share the
        # same database connection pool
        session.close()
        nesp.db.connect.engine.dispose()
        # Process all the species in parallel
        for result, error in tqdm(run_parallel(process, tasks, use_processes = True), total = len(tasks)):
            if error:
                print error

def reproject(geom, src_proj, dest_proj):
    fn = partial(pyproj.transform, src_proj, dest_proj)
    return transform(fn, geom)


def get_core_range_geometry(session, taxon_id):
    rows = session.execute("""SELECT ST_AsBinary(geometry) FROM taxon_range WHERE taxon_id = :taxon_id AND range_id = 1""",
        { 'taxon_id': taxon_id }).fetchall()
    geom = GeometryCollection([shapely.wkb.loads(row[0]) for row in rows])
    return to_multipolygon(geom)

def get_taxon_source_combinations(session, data_type, species):
    if data_type == 1:
        sql = """SELECT DISTINCT taxon_id, source_id
            FROM t1_survey, t1_sighting
            WHERE survey_id = t1_survey.id"""
    else:
        sql = """SELECT DISTINCT t2_ultrataxon_sighting.taxon_id, t2_survey.source_id
            FROM t2_survey, t2_sighting, t2_ultrataxon_sighting
            WHERE t2_survey.id = t2_sighting.survey_id
            AND t2_sighting.id = t2_ultrataxon_sighting.sighting_id"""

    tasks = session.execute(sql).fetchall()

    if species == None:
        # Convert to tuples
        tasks = [(taxon_id, source_id) for taxon_id, source_id in tasks]
    if species != None:
        # Filter to desired species if necessary
        taxa = set(taxon_id for (taxon_id,) in session.execute("SELECT id FROM taxon WHERE spno IN (:species)", { 'species': species }))
        tasks = [(taxon_id, source_id) for taxon_id, source_id in tasks if taxon_id in taxa]

    return tasks

def get_raw_points(session, data_type, taxon_id, source_id):
    if data_type == 1:
        sql = """SELECT DISTINCT ST_X(coords), ST_Y(coords)
        FROM t1_survey, t1_sighting
        WHERE survey_id = t1_survey.id
        AND source_id = :source_id
        AND taxon_id = :taxon_id"""
    else:
        sql = """SELECT DISTINCT ST_X(coords), ST_Y(coords)
        FROM t2_survey, t2_sighting, t2_ultrataxon_sighting
        WHERE survey_id = t2_survey.id
        AND sighting_id = t2_sighting.id
        AND source_id = :source_id
        AND t2_ultrataxon_sighting.taxon_id = :taxon_id"""

    xys = session.execute(sql, { 'taxon_id': taxon_id, 'source_id': source_id }).fetchall()

    return [Point(x, y) for x, y in xys]


from shapely.ops import transform
import pyproj
from shapely.geometry import shape, Point, GeometryCollection
from tsx.geo import to_multipolygon
from tsx.util import run_parallel, sql_list_placeholder, sql_list_argument
from tsx.db import get_session
import tsx.db.connect
import tsx.config
from tqdm import tqdm
import logging
import shapely.wkb
import binascii
from sqlalchemy import text

from tsx.processing.alpha_hull import make_alpha_hull

import fiona

log = logging.getLogger(__name__)

db_proj = pyproj.Proj('EPSG:4326') # Database always uses WGS84
working_proj = pyproj.Proj('EPSG:3112') # GDA94 / Geoscience Australia Lambert - so that we can buffer in metres
to_working_transformer = pyproj.Transformer.from_proj(db_proj, working_proj, always_xy=True)
to_db_transformer = pyproj.Transformer.from_proj(working_proj, db_proj, always_xy=True)

def process_database(species = None, commit = False):
    """
    Calculates spatial representativeness using alpha hulls

    Generates alpha hulls from each source x taxon combination

    Intersects alpha hulls with range layers, and then calculates percentage of range covered
    """
    session = get_session()

    if commit:
        if species == None:
            session.execute(text("DELETE FROM taxon_source_alpha_hull"))
        else:
            session.execute(text("""DELETE FROM taxon_source_alpha_hull
                WHERE taxon_id IN (SELECT id FROM taxon WHERE spno IN (%s))""" % sql_list_placeholder('species', species)),
                sql_list_argument('species', species))
        session.commit()

    # Load coastal shapefile
    coastal_shape_filename = tsx.config.config.get("processing.alpha_hull", "coastal_shp")
    with fiona.Env(OSR_WKT_FORMAT="WKT2_2018"), fiona.open(coastal_shape_filename, 'r') as coastal_shape:
        # Convert from fiona dictionary to shapely geometry and reproject
        shp_to_working_transformer = pyproj.Transformer.from_proj(pyproj.CRS.from_wkt(coastal_shape.crs_wkt), working_proj, always_xy=True)
        coastal_shape = reproject(shape(coastal_shape[0]['geometry']), shp_to_working_transformer)
        # Simplify coastal boundary - makes things run ~20X faster
        log.info("Simplifying coastal boundary")
        coastal_shape = coastal_shape.buffer(10000).simplify(10000)

    log.info("Generating alpha shapes")

    for data_type in 1,2:
        log.info("Processing type %s data" % data_type)

        taxa = get_taxa(session, data_type, species)

        tasks = [(taxon_id, coastal_shape, data_type, commit) for taxon_id in taxa]

        # This is important because we are about to spawn child processes, and this stops them attempting to share the
        # same database connection pool
        session.close() # TODO: not sure if this is needed now

        # Process all the species in parallel
        for result, error in tqdm(run_parallel(process, tasks), total = len(tasks)):
            if error:
                print(error)

# Process a single species.
# This gets run off the main thread.
def process(taxon_id, coastal_shape, data_type, commit):
    session = get_session()

    try:
        # Load core range geometry
        core_range_geom = reproject(get_core_range_geometry(session, taxon_id), to_working_transformer).buffer(0).intersection(coastal_shape)

        for source_id in get_source_ids(session, data_type, taxon_id):

            log.info("Processing taxon_id: %s, source_id: %s" % (taxon_id, source_id))

            # Get raw points from DB
            raw_points = get_raw_points(session, data_type, taxon_id, source_id)

            empty = len(raw_points) < 4

            if empty:
                log.info("Taxon %s: not enough points to create alpha hull (%s)" % (taxon_id, len(raw_points)))

            if not empty:
                # Read points from database
                points = [reproject(p, to_working_transformer) for p in raw_points]

                # Generate alpha shape
                alpha_shp = make_alpha_hull(
                    points = points,
                    coastal_shape = None,
                    thinning_distance = tsx.config.config.getfloat('processing.alpha_hull', 'thinning_distance'),
                    alpha = tsx.config.config.getfloat('processing.alpha_hull', 'alpha'),
                    hullbuffer_distance = tsx.config.config.getfloat('processing.alpha_hull', 'hullbuffer_distance'),
                    isolatedbuffer_distance = tsx.config.config.getfloat('processing.alpha_hull', 'isolatedbuffer_distance'))

                # Clean up geometry
                alpha_shp = alpha_shp.buffer(0)

                if core_range_geom.area == 0:
                    log.info("Core range geometry area is zero")
                    empty = True

                else:
                    # Intersect alpha hull with core range
                    intersected_alpha = to_multipolygon(core_range_geom.intersection(alpha_shp))

                    empty = intersected_alpha.is_empty

            if empty:
                session.execute(text("""INSERT INTO taxon_source_alpha_hull (source_id, taxon_id, data_type, core_range_area_in_m2, alpha_hull_area_in_m2)
                    VALUES (:source_id, :taxon_id, :data_type, 0, 0)"""), {
                        'source_id': source_id,
                        'taxon_id': taxon_id,
                        'data_type': data_type
                    })
            else:
                session.execute(text("""INSERT INTO taxon_source_alpha_hull (source_id, taxon_id, data_type, geometry, core_range_area_in_m2, alpha_hull_area_in_m2)
                    VALUES (:source_id, :taxon_id, :data_type, ST_GeomFromWKB(_BINARY :geom_wkb), :core_range_area, :alpha_hull_area)"""), {
                        'source_id': source_id,
                        'taxon_id': taxon_id,
                        'data_type': data_type,
                        'geom_wkb': shapely.wkb.dumps(reproject(intersected_alpha, to_db_transformer)),
                        'core_range_area': core_range_geom.area,
                        'alpha_hull_area': intersected_alpha.area
                    })

            if commit:
                session.commit()

    except:
        log.exception("Exception processing alpha hull")
        raise
    finally:
        session.close()

def reproject(geom, transformer):
    return transform(transformer.transform, geom)


def get_core_range_geometry(session, taxon_id):
    rows = session.execute(text("""SELECT HEX(ST_AsBinary(geometry)) FROM taxon_range WHERE taxon_id = :taxon_id AND range_id = 1"""),
        { 'taxon_id': taxon_id }).fetchall()
    geom = GeometryCollection([shapely.wkb.loads(binascii.unhexlify(row[0])) for row in rows])
    return to_multipolygon(geom)

def get_taxa(session, data_type, species):
    if data_type == 1:
        taxa = session.execute(text("""SELECT DISTINCT taxon_id FROM t1_sighting""")).fetchall()
    else:
        taxa = session.execute(text("""SELECT DISTINCT taxon_id FROM aggregated_by_year WHERE data_type = 2""")).fetchall()

    taxa = [taxon_id for (taxon_id,) in taxa]

    if species:
        species_taxa = set(taxon_id for (taxon_id,) in session.execute(text(
            "SELECT DISTINCT id FROM taxon WHERE spno IN ({species})".format(
                species = sql_list_placeholder('species', species)))))
        taxa = [taxon_id for taxon_id in taxa if taxon_id in species_taxa]

    return taxa

def get_source_ids(session, data_type, taxon_id):
    if data_type == 1:
        sql = """SELECT DISTINCT source_id
        FROM t1_survey, t1_sighting
        WHERE survey_id = t1_survey.id
        AND taxon_id = :taxon_id"""
    else:
        sql = """SELECT DISTINCT source_id
        FROM aggregated_by_year
        WHERE data_type = 2
        AND taxon_id = :taxon_id"""

    return [source_id for (source_id,) in session.execute(text(sql), { 'taxon_id': taxon_id }).fetchall()]

def get_raw_points(session, data_type, taxon_id, source_id):
    if data_type == 1:
        sql = """SELECT DISTINCT ST_X(coords), ST_Y(coords)
        FROM t1_survey, t1_sighting
        WHERE survey_id = t1_survey.id
        AND source_id = :source_id
        AND taxon_id = :taxon_id"""
    else:
        sql = """SELECT DISTINCT ST_X(t2_survey.coords), ST_Y(t2_survey.coords)
        FROM aggregated_by_year agg
        JOIN t2_survey ON t2_survey.site_id = agg.site_id
        WHERE agg.data_type = 2
        AND agg.source_id = :source_id
        AND agg.taxon_id = :taxon_id"""

    xys = session.execute(text(sql), { 'taxon_id': taxon_id, 'source_id': source_id }).fetchall()

    return [Point(x, y) for x, y in xys]

from shapely.geometry import Point, Polygon
import shapely.wkb
from tqdm import tqdm
from tsx.db import get_session, Taxon, T2UltrataxonSighting
import tsx.db.connect
from tsx.util import run_parallel, sql_list_placeholder, sql_list_argument
from tsx.geo import point_intersects_geom
import logging
import binascii

log = logging.getLogger(__name__)

def process_database(species = None, commit = False):
    session = get_session()

    # Just get taxa that have range polygons
    if species == None:
        taxa = session.execute("SELECT DISTINCT taxon_id FROM taxon_range").fetchall()
    else:
        taxa = session.execute("SELECT DISTINCT taxon_id FROM taxon_range, taxon WHERE taxon_id = taxon.id AND spno IN (%s)" % sql_list_placeholder('species', species),
            sql_list_argument('species', species)).fetchall()

    # Unwrap tuple
    taxa = [taxon_id for (taxon_id,) in taxa]

    # Delete old results
    if commit and len(taxa) > 0:
        # session.execute("DELETE FROM t2_ultrataxon_sighting WHERE taxon_id IN (:taxa)", { 'taxa': taxa })
        session.execute("DELETE FROM t2_ultrataxon_sighting WHERE taxon_id IN (%s)" % sql_list_placeholder('taxa', taxa), sql_list_argument('taxa', taxa))
        session.commit()

    # Process in parallel
    tasks = [(taxon_id, commit) for taxon_id in taxa]

    # This is important because we are about to spawn child processes, and this stops them attempting to share the
    # same database connection pool
    session.close()
    for result, error in tqdm(run_parallel(process_taxon, tasks), total=len(tasks)):
        if error:
            print(error)


def get_taxon_range_polygons(session, taxon_id):
    return session.execute("""SELECT range_id, breeding_range_id, HEX(ST_AsWKB(geometry))
                        FROM taxon_range
                        WHERE taxon_id = :taxon_id
                        """, { 'taxon_id': taxon_id }).fetchall()

def process_taxon(taxon_id, commit):
    try:
        session = get_session()

        taxon = session.query(Taxon).get(taxon_id)

        if taxon is None:
            log.info("Could not find taxon with id = %s, skipping", taxon_id)
            log.info("(This means a range polygon exists for a non-existent taxon, which may be due to an error in the range polygons or because the taxonomy has changed)")
            return

        for range_id, breeding_range_id, geom_wkb in get_taxon_range_polygons(session, taxon.id):
            if not taxon.ultrataxon:
                log.info("Skipping range polygon for non-ultrataxon: %s" % taxon.id)
                continue

            # tqdm.write("Taxon: %s, range: %s" % (taxon.id, range_id))

            cache = {}

            geom = shapely.wkb.loads(binascii.unhexlify(geom_wkb)).buffer(0) # Ensure valid

            bounds_wkb = shapely.wkb.dumps(Polygon.from_bounds(*geom.bounds))

            # Get all sightings matching that taxon
            q = session.execute("""SELECT t2_sighting.id, ST_X(coords), ST_Y(coords)
                FROM t2_sighting, t2_survey
                WHERE t2_sighting.survey_id = t2_survey.id
                AND t2_sighting.taxon_id = :taxon_id
                AND t2_sighting.taxon_id NOT IN (SELECT taxon_id FROM t2_ultrataxon_sighting WHERE sighting_id = t2_sighting.id)
                AND MBRContains(ST_GeomFromWKB(_BINARY :bounds_wkb), coords) """, {
                'taxon_id': taxon.id,
                'bounds_wkb': bounds_wkb
            })

            records = []

            for sighting_id, x, y in q.fetchall():
                if point_intersects_geom(geom, x, y, cache):
                    records.append(T2UltrataxonSighting(
                        sighting_id = sighting_id,
                        taxon_id = taxon.id,
                        range_id = range_id,
                        generated_subspecies = False
                    ))
                    # Would this help improve concurrency?:
                    # if len(records) > 1000:
                    #     session.bulk_save_objects(records)
                    #     records = []

            if taxon.taxon_level.description == 'ssp':
                # Get parent taxa (species) sightings
                q = session.execute("""SELECT t2_sighting.id, ST_X(coords), ST_Y(coords)
                    FROM t2_sighting, t2_survey, taxon taxon_ssp, taxon taxon_sp
                    WHERE t2_sighting.survey_id = t2_survey.id
                    AND t2_sighting.taxon_id = taxon_sp.id
                    AND taxon_ssp.id NOT IN (SELECT taxon_id FROM t2_ultrataxon_sighting WHERE sighting_id = t2_sighting.id)
                    AND taxon_sp.taxon_level_id = (SELECT id FROM taxon_level WHERE description = 'sp')
                    AND taxon_sp.spno = taxon_ssp.spno
                    AND taxon_ssp.id = :taxon_id
                    AND MBRContains(ST_GeomFromWKB(_BINARY :bounds_wkb), coords) """, {
                    'taxon_id': taxon.id,
                    'bounds_wkb': bounds_wkb
                })

                for sighting_id, x, y in q.fetchall():
                    if point_intersects_geom(geom, x, y, cache):
                        records.append(T2UltrataxonSighting(
                            sighting_id = sighting_id,
                            taxon_id = taxon.id,
                            range_id = range_id,
                            generated_subspecies = True
                        ))
                        # Would this help improve concurrency?:
                        # if len(records) > 1000:
                        #     session.bulk_save_objects(records)
                        #     records = []

            session.bulk_save_objects(records)
        if commit:
            session.commit()
    except Exception as e:
        log.exception('Exception in range and ultrataxon processing')
        raise
    finally:
        session.close()

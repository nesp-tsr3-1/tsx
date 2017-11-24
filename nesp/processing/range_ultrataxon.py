from shapely.geometry import Point, Polygon
import shapely.wkb
from tqdm import tqdm
from nesp.db import get_session, Taxon, T2UltrataxonSighting
from nesp.util import run_parallel
from nesp.geo import point_intersects_geom
import logging

log = logging.getLogger(__name__)

def process_database(species = None, commit = False):
    session = get_session()

    # Just get taxa that have range polygons
    if species == None:
        taxa = session.execute("SELECT DISTINCT taxon_id FROM taxon_range").fetchall()
    else:
        taxa = session.execute("SELECT DISTINCT taxon_id FROM taxon_range, taxon WHERE taxon_id = taxon.id AND spno IN :species",
            { 'species': species}).fetchall()

    # Unwrap tuple
    taxa = [taxon_id for (taxon_id,) in taxa]

    # Delete old results
    if commit:
        session.execute("DELETE FROM t2_ultrataxon_sighting WHERE taxon_id IN :taxa", { 'taxa': taxa })
        session.commit()

    # Process in parallel
    tasks = [(taxon_id, commit) for taxon_id in taxa]

    for result, error in tqdm(run_parallel(process_taxon, tasks), total=len(tasks)):
        if error:
            print error


def get_taxon_range_polygons(session, taxon_id):
    return session.execute("""SELECT range_id, breeding_range_id, ST_AsWKB(geometry)
                        FROM taxon_range
                        WHERE taxon_id = :taxon_id
                        """, { 'taxon_id': taxon_id }).fetchall()

def process_taxon(taxon_id, commit):
    try:
        session = get_session()

        taxon = session.query(Taxon).get(taxon_id)

        for range_id, breeding_range_id, geom_wkb in get_taxon_range_polygons(session, taxon.id):
            if not taxon.ultrataxon:
                log.warning("Unexpected range polygon for non-ultrataxon: %s" % taxon.id)
                continue

            # tqdm.write("Taxon: %s, range: %s" % (taxon.id, range_id))

            cache = {}

            geom = shapely.wkb.loads(geom_wkb).buffer(0) # Ensure valid

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
                        generated_subspecies = False # TODO: populate this properly for Birdata sightings
                    ))

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

            session.bulk_save_objects(records)
        session.commit()
    except Exception as e:
        log.exception('Exception in range and ultrataxon processing')
        raise
    finally:
        session.close()

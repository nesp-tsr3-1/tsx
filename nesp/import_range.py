from nesp.db import Taxon, TaxonLevel, TaxonStatus, get_session
import os
import logging
import sys
import argparse
from tqdm import tqdm
import re
import shapely.wkb
from nesp.geo import subdivide_geometry, to_multipolygon, count_points, reproject
from shapely.geometry import MultiPolygon, Polygon, shape
import fiona
import time
import pyproj

log = logging.getLogger(__name__)
insert_subdivided = False

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import species range polygons into NESP database')
	parser.add_argument('dir', type=str, help='Directory containing species range shapefiles')
	args = parser.parse_args()

	session = get_session()

	filenames = [f for f in os.listdir(args.dir) if f.endswith('.shp')]

	for filename in tqdm(filenames):
		spno = int(filename[0:-4])
		try:
			with fiona.open(os.path.join(args.dir, filename), encoding = 'Windows-1252') as shp:
				process_shp(session, spno, shp)
		except KeyboardInterrupt:
			log.info("Aborting - no changes saved")
			return

	session.commit()

_taxon_re = re.compile('(u?[0-9]+)([a-z](\.[a-z])*)?')

def process_shp(session, spno, shp):
	for feature in shp:
		try:
			props = feature['properties']
			# Convert property names to uppercase
			props = { key.upper(): props[key] for key in props }

			if spno != props['SPNO']:
				log.error('SPNO does not match %s != %s' % (spno, props['SPNO']))
				return

			if props['RNGE'] in (8,9): # TODO - investigate what these numbers mean
				return

			taxon_id = props['TAXONID']

			parts = _taxon_re.match(taxon_id)

			if parts is None:
				log.error("Invalid taxon id format: %s" % taxon_id)
				return

			prefix = parts.group(1)
			suffix = parts.group(2) or ''

			geometry = shape(feature['geometry'])
			if type(geometry) == Polygon:
				geometry = MultiPolygon([geometry])

			geometry = reproject(geometry, pyproj.Proj(shp.crs), pyproj.Proj('+init=EPSG:4326'))

			for s in suffix.split("."):
				taxon_exists = len(session.execute("SELECT 1 FROM taxon WHERE id = :id", { 'id': prefix + s }).fetchall()) > 0
				if taxon_exists:
					session.execute("""INSERT INTO taxon_range (taxon_id, range_id, breeding_range_id, geometry) VALUES
						(:taxon_id, :range_id, :breeding_range_id, ST_GeomFromWKB(_BINARY :geom_wkb))""", {
							'taxon_id': prefix + s,
							'range_id': props['RNGE'] or None,
							'breeding_range_id': props['BRRNGE'] or None,
							'geom_wkb': shapely.wkb.dumps(geometry)
						}
					)

					if insert_subdivided:
						for geom in subdivide_geometry(geometry.buffer(0)):
							geom = to_multipolygon(geom)
							if not geom.is_empty:
								session.execute("""INSERT INTO taxon_range_subdiv (taxon_id, range_id, breeding_range_id, geometry) VALUES
									(:taxon_id, :range_id, :breeding_range_id, ST_GeomFromWKB(_BINARY :geom_wkb))""", {
										'taxon_id': prefix + s,
										'range_id': props['RNGE'] or None,
										'breeding_range_id': props['BRRNGE'] or None,
										'geom_wkb': shapely.wkb.dumps(to_multipolygon(geom))
									}
								)

		except:
			log.error("Error processing row: %s" % props)
			raise


if __name__ == '__main__':
	main()

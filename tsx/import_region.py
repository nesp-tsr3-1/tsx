from tsx.db import get_session
import logging
import sys
import argparse
from tqdm import tqdm
import shapely.wkb
import shapely.ops
from tsx.geo import to_multipolygon, subdivide_geometry
from shapely.geometry import shape
from fiona.transform import transform_geom
import fiona
import pyproj
from sqlalchemy import text

log = logging.getLogger(__name__)

def to_2d(x, y, z):
    return tuple(filter(None, [x, y]))

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import regions from shapefile')
	parser.add_argument('filename', type=str, help='Shapefile containing regions')
	args = parser.parse_args()

	session = get_session()

	session.execute(text("DELETE FROM t1_survey_region"))

	with fiona.open(args.filename, encoding = 'Windows-1252') as shp:
		for index, feature in enumerate(tqdm(shp)):
			props = feature['properties']

			geometry = shape(transform_geom(shp.crs, 'EPSG:4326', feature['geometry']))
			geometry = geometry.buffer(0)

			session.execute(text("""INSERT INTO region (id, name, geometry, state, positional_accuracy_in_m)
					VALUES (:id, :name, ST_GeomFromWKB(_BINARY :geometry_wkb), :state, :positional_accuracy_in_m)"""), {
						'id': index,
						'name': props['RegName'],
						'geometry_wkb': shapely.wkb.dumps(to_multipolygon(geometry)),
						'state': props['StateName'],
						'positional_accuracy_in_m': int(props['Accuracy'])
					})

			for geometry in subdivide_geometry(geometry):

				session.execute(text("""INSERT INTO region_subdiv (id, name, geometry)
					VALUES (:id, :name, ST_GeomFromWKB(_BINARY :geometry_wkb))"""), {
						'id': index,
						'name': props['RegName'],
						'geometry_wkb': shapely.wkb.dumps(to_multipolygon(geometry))
					})

	log.info("Updating t1_survey_region (this may take a while)")
	session.execute(text("CALL update_t1_survey_region(NULL)"))

	session.commit()

if __name__ == '__main__':
	main()

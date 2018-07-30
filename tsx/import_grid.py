from tsx.db import get_session
import logging
import sys
import argparse
from tqdm import tqdm
import shapely.wkb
from tsx.geo import reproject_fn, to_multipolygon
from shapely.geometry import shape
import fiona
import pyproj

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import grid cells from shapefile')
	parser.add_argument('filename', type=str, help='Shapefile containing grid cells')
	args = parser.parse_args()

	session = get_session()

	with fiona.open(args.filename, encoding = 'Windows-1252') as shp:
		reproject = reproject_fn(pyproj.Proj(shp.crs), pyproj.Proj('+init=EPSG:4326'))
		for feature in tqdm(shp):
			props = feature['properties']
			geometry = reproject(shape(feature['geometry']))

			session.execute("""INSERT INTO grid_cell (id, geometry)
				VALUES (:search_type_id, ST_GeomFromWKB(_BINARY :geometry_wkb))""", {
					'search_type_id': props['GridID'],
					'geometry_wkb': shapely.wkb.dumps(geometry)
				})

	session.commit()

if __name__ == '__main__':
	main()

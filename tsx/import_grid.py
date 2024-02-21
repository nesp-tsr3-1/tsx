from tsx.db import get_session
import logging
import sys
import argparse
from tqdm import tqdm
import shapely.wkb
from tsx.geo import open_shapefile, to_multipolygon
from shapely.geometry import shape
import pyproj
from sqlalchemy import text

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import grid cells from shapefile')
	parser.add_argument('filename', type=str, help='Shapefile containing grid cells')
	args = parser.parse_args()

	session = get_session()

	with open_shapefile(args.filename, 'EPSG:4326') as (shp, reproject):
		for feature in tqdm(shp):
			props = feature['properties']
			geometry = reproject(shape(feature['geometry']))

			session.execute(text("""INSERT INTO grid_cell (id, geometry)
				VALUES (:search_type_id, ST_GeomFromWKB(_BINARY :geometry_wkb))"""), {
					'search_type_id': props['GridID'],
					'geometry_wkb': shapely.wkb.dumps(geometry)
				})

	session.commit()

if __name__ == '__main__':
	main()

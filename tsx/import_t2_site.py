from tsx.db import get_session
import logging
import sys
import argparse
from tqdm import tqdm
import shapely.wkb
from tsx.geo import open_shapefile, to_multipolygon
from shapely.geometry import shape
from shapely.ops import transform
import pyproj

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Type 2 sites from shapefile')
	parser.add_argument('filename', type=str, help='Shapefile containing type 2 site polygons')
	args = parser.parse_args()

	session = get_session()

	with open_shapefile(args.filename, dest_crs='EPSG:4326') as (shp, reproject):
		for feature in tqdm(shp):
			props = feature['properties']
			geometry = to_multipolygon(reproject(shape(feature['geometry'])))

			session.execute("""INSERT INTO t2_site (search_type_id, geometry)
				VALUES (:search_type_id, ST_GeomFromWKB(_BINARY :geometry_wkb))""", {
					'search_type_id': props['SiteType'],
					'geometry_wkb': shapely.wkb.dumps(geometry)
				})

	session.commit()

if __name__ == '__main__':
	main()

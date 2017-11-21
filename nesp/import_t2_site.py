from nesp.db import get_session
import logging
import sys
import argparse
from tqdm import tqdm
import shapely.wkb
from nesp.geo import reproject_fn, to_multipolygon
from shapely.geometry import shape
import fiona
import pyproj

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Type 2/3 sites from shapefile')
	parser.add_argument('filename', type=str, help='Shapefile containing type 2/3 site polygons')
	args = parser.parse_args()

	session = get_session()

	with fiona.open(args.filename, encoding = 'Windows-1252') as shp:
		reproject = reproject_fn(pyproj.Proj(shp.crs), pyproj.Proj('+init=EPSG:4326'))
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

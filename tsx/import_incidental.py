from tsx.db import get_session
import logging
import sys
import argparse
import csv
from tqdm import tqdm
from shapely.geometry import Point
import shapely.wkb
from sqlalchemy import text

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import incidental sightings')
	parser.add_argument('filename', type=str, help='Incidental sightings file (CSV)')
	args = parser.parse_args()

	session = get_session()

	spno_map = { spno: taxon_id for spno, taxon_id in session.execute(
		text("""SELECT spno, taxon.id
			FROM taxon, taxon_level
			WHERE taxon_level.id = taxon_level_id
			AND taxon_level.description = 'sp'""")).fetchall()
	}

	session.execute(text("""DELETE FROM incidental_sighting"""));

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		row_count = sum(1 for row in reader)

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		rows = []

		def flush_rows():
			session.execute(text("INSERT INTO incidental_sighting (taxon_id, coords) VALUES (:taxon_id, ST_GeomFromWKB(_BINARY :coords))"), rows)
			del rows[:]

		for row in tqdm(reader, total = row_count):
			spno = int(row['SpNo'])
			x = float(row['Longitude'])
			y = float(row['Latitude'])
			if spno in spno_map:
				rows.append({
					'taxon_id': spno_map[spno],
					'coords': shapely.wkb.dumps(Point(x, y))
				})
			if len(rows) > 4000:
				flush_rows()

		flush_rows()

	session.commit()



if __name__ == '__main__':
	main()

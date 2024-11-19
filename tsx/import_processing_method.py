from tsx.db import get_session
import logging
import sys
import argparse
import csv
from tqdm import tqdm
from sqlalchemy import text

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import processing method')
	parser.add_argument('--relax', action='store_true', dest='relax', help="Just use source/search type descriptions and ignore id")
	parser.add_argument('filename', type=str, help='Processing method file (CSV)')
	args = parser.parse_args()

	session = get_session()

	source_by_id = { source_id: desc for source_id, desc in session.execute(text("SELECT id, description FROM source")).fetchall() }
	search_type_by_id = { search_type_id: desc for search_type_id, desc in session.execute(text("SELECT id, description FROM search_type")).fetchall() }

	session.execute(text("DELETE FROM processing_method"))

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		for row in tqdm(list(reader)):
			if row['response_variable_type_id'] in ('0', ''):
				continue
			if row.get('positional_accuracy_threshold_in_m', '') == '':
				row['positional_accuracy_threshold_in_m'] = None

			source_id = int(row['source_id'])

			if source_id not in source_by_id:
				raise ValueError("Unrecognized source_id: %s" % source_id)


			if 'source_description' in row and source_by_id[source_id] != row['source_description']:
				msg = "Source description does not match (source_id: %s, source_description: %s, database description: %s)" % (
					row['source_id'], row['source_description'], source_by_id[source_id])
				if args.relax:
					log.info(msg)
				else:
					raise ValueError(msg)

			search_type_id = int(row['search_type_id'])

			if search_type_id not in search_type_by_id:
				raise ValueError("Unrecognized search_type_id: %s" % search_type_id)

			if 'search_type_description' in row and search_type_by_id[search_type_id] != row['search_type_description']:
				msg = "Search type description does not match (search_type_id: %s, search_type_description: %s, database description: %s)" % (
					row['search_type_id'], row['search_type_description'], search_type_by_id[search_type_id])
				if args.relax:
					log.info(msg)
				else:
					raise ValueError(msg)

			if int(row['data_type']) not in (1,2):
				raise ValueError("Invalid data type (%s): must be 1 or 2", row['data_type'])

			session.execute(text("""INSERT INTO processing_method (
					taxon_id,
					unit_id,
					source_id,
					search_type_id,
					data_type,
					response_variable_type_id,
					positional_accuracy_threshold_in_m
				) VALUES (
					:taxon_id,
					:unit_id,
					:source_id,
					:search_type_id,
					:data_type,
					:response_variable_type_id,
					:positional_accuracy_threshold_in_m
				)"""), row)

	session.commit()

if __name__ == '__main__':
	main()

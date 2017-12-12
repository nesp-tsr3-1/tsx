from nesp.db import get_session
import logging
import sys
import argparse
import csv

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import processing method')
	parser.add_argument('--relax', action='store_true', dest='relax', help="Just use source/search type descriptions and ignore id")
	parser.add_argument('filename', type=str, help='Processing method file (CSV)')
	args = parser.parse_args()

	session = get_session()

	source_by_id = { source_id: desc for source_id, desc in session.execute("SELECT id, description FROM source").fetchall() }
	search_type_by_id = { search_type_id: desc for search_type_id, desc in session.execute("SELECT id, description FROM search_type").fetchall() }

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		for row in reader:
			if row['experimental_design_type_id'] in ('0', ''):
				continue
			if row['response_variable_type_id'] in ('0', ''):
				continue
			if row['positional_accuracy_threshold_in_m'] == '':
				row['positional_accuracy_threshold_in_m'] = None

			if args.relax:
				r = session.execute("SELECT id FROM source WHERE description = :description", { 'description': row['source_description'] }).fetchall()
				if len(r) > 0:
					row['source_id'] = r[0][0]
				else:
					continue

				r = session.execute("SELECT id FROM search_type WHERE description = :description", { 'description': row['search_type_description'] }).fetchall()
				if len(r) > 0:
					row['search_type_id'] = r[0][0]
				else:
					continue
			else:
				if source_by_id.get(row['source_id'], None) != row['source_description']:
					raise ValueError("Unrecognized source id/description combination (%s, %s)" % (row['source_id'], row['source_description']))

				if search_type_by_id.get(row['search_type_id'], None) != row['search_type_description']:
					raise ValueError("Unrecognized search type id/description combination (%s, %s)" % (row['search_type_id'], row['search_type_description']))


			if int(row['DataType']) not in (1,2):
				raise ValueError("Invalid data type (%s): must be 1 or 2", row['DataType'])

			session.execute("""INSERT INTO processing_method (
					taxon_id,
					unit_id,
					source_id,
					search_type_id,
					data_type,
					experimental_design_type_id,
					response_variable_type_id,
					positional_accuracy_threshold_in_m
				) VALUES (
					:taxon_id,
					:unit_id,
					:source_id,
					:search_type_id,
					:DataType,
					:experimental_design_type_id,
					:response_variable_type_id,
					:positional_accuracy_threshold_in_m
				)""", row)

	session.commit()

if __name__ == '__main__':
	main()

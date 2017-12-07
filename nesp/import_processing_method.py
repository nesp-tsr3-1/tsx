from nesp.db import get_session
import logging
import sys
import argparse
import csv

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import processing method')
	parser.add_argument('--type', dest='data_type', choices=[1,2], type=int, help='Type of data (1 or 2)', required=True)
	parser.add_argument('filename', type=str, help='Processing method file (CSV)')
	args = parser.parse_args()

	session = get_session()

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		for row in reader:
			if args.data_type == 1:
				# source_exists = len(session.execute("SELECT 1 FROM source WHERE id = :id", { 'id': row['source_id']}).fetchall()) > 0
				# if not source_exists:
				# 	continue

				session.execute("""INSERT INTO processing_method (taxon_id, unit_id, source_id, search_type_id, data_type, experimental_design_type_id, response_variable_type_id)
					VALUES (:taxon_id, :unit_id, :source_id, :search_type_id, 1, :experimental_design_type_id, :response_variable_type_id)""",
					row)
			else:
				raise Exception("Not implemented yet")

	session.commit()

if __name__ == '__main__':
	main()

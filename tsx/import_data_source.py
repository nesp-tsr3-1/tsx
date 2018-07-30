from tsx.db import get_session
import logging
import sys
import argparse
import csv

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import data source information')
	parser.add_argument('--relax', action='store_true', dest='relax', help="Ignore invalid source ids")
	parser.add_argument('filename', type=str, help='Processing method file (CSV)')
	args = parser.parse_args()

	session = get_session()

	session.execute("DELETE FROM data_source");

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		for row in reader:
			data = {
				'source_id': row['SourceID'],
				'taxon_id': row['TaxonID'],
				'data_agreement_id': row['DataAgreement'] or None,
				'objective_of_monitoring_id': row['ObjectiveOfMonitoring'] or None,
				'no_absences_recorded': row['NoAbsencesRecorded'] or 0,
				'standardisation_of_method_effort_id': row['StandardisationOfMethodEffort'] or None,
				'consistency_of_monitoring_id': row['ConsistencyOfMonitoring'] or None
			}

			r = session.execute("SELECT 1 FROM source WHERE id = :id", { 'id': data['source_id'] }).fetchall()
			if len(r) == 0:
				if args.relax:
					log.warn("Skipping unknown source id: %s" % data['source_id'])
					continue
				else:
					raise ValueError("Invalid source id: %s" % data['source_id'])


			session.execute("""INSERT INTO data_source (
					source_id,
					taxon_id,
					data_agreement_id,
					objective_of_monitoring_id,
					no_absences_recorded,
					standardisation_of_method_effort_id,
					consistency_of_monitoring_id
				) VALUES (
					:source_id,
					:taxon_id,
					:data_agreement_id,
					:objective_of_monitoring_id,
					:no_absences_recorded,
					:standardisation_of_method_effort_id,
					:consistency_of_monitoring_id
				)""",
				data
			)


	session.commit()

if __name__ == '__main__':
	main()

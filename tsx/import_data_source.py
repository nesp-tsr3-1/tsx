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
	parser.add_argument('--update-source-table', action='store_true', dest='update_source_table', help="Also update `source` table with authors, provider and description information")
	parser.add_argument('filename', type=str, help='Data source file  (aka master list) (CSV)')
	args = parser.parse_args()

	session = get_session()

	session.execute("DELETE FROM data_source");

	with open(args.filename) as f:
		reader = csv.DictReader(f)
		for row in reader:
			data = {
				'source_id': row['SourceID'],
				'taxon_id': row['TaxonID'],
				'data_agreement_id': row.get('AgreementSigned') or None,
				'objective_of_monitoring_id': lookup(row, 'ObjectiveOfMonitoring'),
				'absences_recorded': get_bool(row, 'AbsencesRecorded', True, unknown_value_default=True),
				'standardisation_of_method_effort_id': lookup(row, 'StandardisationOfMethodEffort', optional=True),
				'consistency_of_monitoring_id': lookup(row, 'ConsistencyOfMonitoring', optional=True),
				'start_year': row.get('StartYear') or None,
				'end_year': row.get('EndYear') or None,
				'exclude_from_analysis': get_bool(row, 'NotInIndex', False, unknown_value_default=True, optional=True),
				'suppress_aggregated_data': get_bool(row, 'SuppressAggregatedDataUntil', False, unknown_value_default=True, optional=True)
			}

			# In relaxed mode, silently skip rows without SourceID value
			if args.relax and row['SourceID'].strip() in ('', 'NULL', 'NA'):
				continue

			r = session.execute("SELECT 1 FROM source WHERE id = :id", { 'id': data['source_id'] }).fetchall()
			if len(r) == 0:
				if args.relax:
					log.warning("Skipping unknown source id: %s" % data['source_id'])
					continue
				else:
					raise ValueError("Invalid source id: %s" % data['source_id'])

			if args.update_source_table:
				def strip_and_warn(s):
					stripped = s.strip(". ")
					if s != stripped:
						log.warning("Stripping leading/trailing space/periods from '%s'", s)
					return stripped

				data['authors'] = strip_and_warn(row['Authors'])
				data['provider'] = strip_and_warn(row['SourceProvider'])
				data['description'] = strip_and_warn(row['SourceDesc'])

				# TODO: Not sure if SourceName should be imported into source.description?
				session.execute("""UPDATE source SET authors = :authors, provider = :provider, description = :description WHERE id = :source_id""", data)

			session.execute("""INSERT INTO data_source (
					source_id,
					taxon_id,
					data_agreement_id,
					objective_of_monitoring_id,
					absences_recorded,
					standardisation_of_method_effort_id,
					consistency_of_monitoring_id,
					start_year,
					end_year,
					exclude_from_analysis,
					suppress_aggregated_data
				) VALUES (
					:source_id,
					:taxon_id,
					:data_agreement_id,
					:objective_of_monitoring_id,
					:absences_recorded,
					:standardisation_of_method_effort_id,
					:consistency_of_monitoring_id,
					:start_year,
					:end_year,
					:exclude_from_analysis,
					:suppress_aggregated_data
				)""",
				data
			)

	session.commit()


LOOKUPS = {
	'ObjectiveOfMonitoring': {
		'Monitoring for targeted conservation management': 4,
		'Monitoring for general conservation management – ‘surveillance’ monitoring.': 3,
		'Baseline monitoring': 2,
		'Monitoring for community engagement': 1
	},
	'ConsistencyOfMonitoring': {
		'Balanced; all (or virtually all) sites surveyed in each year sampled (no, or virtually no, site turnover)': 4,
		'Imbalanced (low turnover); sites surveyed consistently through time as established, but new sites are added to program with time': 3,
		'Imbalanced (high turnover); new sites are surveyed with time, but monitoring of older sites is often not maintained': 2,
		'Highly Imbalanced (very high turnover); different sites surveyed in different sampling periods. Sites are generally not surveyed consistently through time (highly biased)': 1
	},
	'StandardisationOfMethodEffort': {
		'Pre-defined sites/plots surveyed repeatedly through time using a single standardised method and effort across the whole monitoring program': 6,
		'Pre-defined sites/plots surveyed repeatedly through time with methods and effort standardised within site units, but not across program - i.e. different sites surveyed have different survey effort/methods': 5,
		'Pre-defined sites/plots surveyed repeatedly through time with varying methods and effort': 4,
		'Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping possible - e.g. a lot of fixed area/time searches conducted within a region but not at pre-defined sites': 3,
		'Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping not possible': 2,
		'Unstandardised methods/effort, surveys not site-based': 1
	}
}

def get_bool(row, column, default=None, unknown_value_default=None, optional=False):
	raw_value = row.get(column)
	if optional and raw_value is None:
		return default

	raw_value = raw_value.strip()
	value = raw_value.lower()

	if value in ('1', 'yes', 'true', 'y', 't'):
		return True
	if value in ('0', 'no', 'false', 'n', 'f'):
		return False
	if value in ('', 'na', 'null'):
		return default
	else:
		log.warning("Unknown value for %s: '%s', defaulting to %s" % (column, raw_value, unknown_value_default))
		return unknown_value_default

def lookup(row, column, optional=False):
	value = row.get(column)

	if optional and value is None:
		return None

	lookup = LOOKUPS[column]

	if value in ('', 'NA', '0'):
		return None
	elif value.isdigit() and int(value) in lookup.values():
		return value
	elif value in lookup:
		return lookup[value]
	else:
		log.warning("Unknown value for %s: '%s', defaulting to None" % (column, value))
		return None

if __name__ == '__main__':
	main()

from nesp.db import Taxon, TaxonLevel, TaxonStatus, get_session
import os
import logging
import sys
import argparse
import openpyxl

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Taxon spreadsheet into NESP taxon table')
	parser.add_argument('filename', type=str, help='Taxon spreadsheet (Excel format)')
	args = parser.parse_args()

	session = get_session()

	wb = openpyxl.load_workbook(args.filename)
	ws = wb['TaxonList']

	for i, row in enumerate(ws.rows):
		row = [cell.value for cell in row]
		if i == 0:
			headers = row
		else:
			row = dict(zip(headers, row))

			for key in row:
				if type(row[key]) in (str, unicode):
					row[key] = row[key].strip()

			if len(str(row['TaxonID'])) > 6:
				log.info("Skipping long taxon id %s" % row['TaxonID'])
				continue

			if str(row['SpNo']) not in str(row['TaxonID']):
				raise ValueError("Invalid SpNo/TaxonID combination: %s/%s" % (row['SpNo'], row['TaxonID']))

			try:
				taxon = Taxon(
					id = row['TaxonID'],
					ultrataxon = row['UltrataxonID'] == 'u',
					taxon_level = get_or_create(session, TaxonLevel, description = row['Taxon Level']),
					spno = row['SpNo'],
					common_name = row['Taxon name'],
					scientific_name = row['Taxon scientific name'],
					family_common_name = row['Family common name'],
					family_scientific_name = row['Family scientific name'],
					order = row['Order'],
					population = row['Population'],
					# TODO - there are status in WLAB like 'Introduced' and 'Vagrant' not in Glenn's list - for now importing as NULL
					aust_status = session.query(TaxonStatus).filter_by(description = row['AustralianStatus']).one_or_none(),

					experimental_design_type_id = row['experimental_design_type_id'],
					response_variable_type_id = row['response_variable_type_id'],
					positional_accuracy_threshold_in_m = row['spatial_accuracy_threshold']
				)
			except:
				print row
				raise

			session.add(taxon)

	session.commit()


# see: https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
def get_or_create(session, model, **kwargs):
	"""
	Gets a single row from the database matching the passed criteria, or creates such a row if none exists
	"""
	instance = session.query(model).filter_by(**kwargs).one_or_none()
	if instance != None:
		return instance
	else:
		instance = model(**kwargs)
		session.add(instance)
		return instance

if __name__ == '__main__':
	main()

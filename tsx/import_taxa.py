from tsx.db import Taxon, TaxonLevel, TaxonStatus, get_session
import os
import logging
import sys
import argparse
import openpyxl

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Taxon spreadsheet into TSX taxon table')
	parser.add_argument('filename', type=str, help='Taxon spreadsheet (Excel format)')
	args = parser.parse_args()

	session = get_session()

	session.execute("SET FOREIGN_KEY_CHECKS = 0")
	session.execute("DELETE FROM taxon")

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
					epbc_status = session.query(TaxonStatus).filter_by(description = row['EPBCStatus']).one_or_none(),
					iucn_status = session.query(TaxonStatus).filter_by(description = row['IUCNStatus']).one_or_none(),
					bird_group = row['BirdGroup'],
					bird_sub_group = row['BirdSubGroup'],
					national_priority = str(row['NationalPriorityTaxa']) == '1'
				)
			except:
				print row
				raise

			session.add(taxon)

	session.execute("SET FOREIGN_KEY_CHECKS = 1")

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

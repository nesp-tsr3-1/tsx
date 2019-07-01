from tsx.db import Taxon, TaxonGroup, TaxonLevel, TaxonStatus, get_session
import os
import logging
import sys
import argparse
import openpyxl
from tqdm import tqdm
from six import text_type

log = logging.getLogger(__name__)

def main():
	logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)-15s %(name)s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Taxon spreadsheet into TSX taxon table')
	parser.add_argument('filename', type=str, help='Taxon spreadsheet (Excel format)')
	args = parser.parse_args()

	session = get_session()

	# We temporarily disable foreign key checks so that we don't have to delete all data from the database
	session.execute("SET FOREIGN_KEY_CHECKS = 0")
	session.execute("DELETE FROM taxon")
	session.execute("DELETE FROM taxon_group")

	print("Loading workbook...")

	wb = openpyxl.load_workbook(args.filename, read_only=True)
	ws = wb['TaxonList']

	for i, row in tqdm(enumerate(ws.rows), total=ws.max_row):
		row = [cell.value for cell in row]
		if i == 0:
			headers = row
		else:
			row = dict(list(zip(headers, row)))

			for key in row:
				if type(row[key]) in (str, text_type):
					row[key] = row[key].strip()

			if len(str(row['TaxonID'])) > 8:
				log.info("Skipping long taxon id %s" % row['TaxonID'])
				continue

			if row['SpNo'] and str(row['SpNo']) not in str(row['TaxonID']):
				raise ValueError("Invalid SpNo/TaxonID combination: %s/%s" % (row['SpNo'], row['TaxonID']))

			taxon_groups = []

			try:
				taxon = Taxon(
					id = row['TaxonID'],
					ultrataxon = row['UltrataxonID'] == 'u',
					taxon_level = get_or_create(session, TaxonLevel, description = row['Taxon Level']) if row['Taxon Level'] else None,
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
					state_status = session.query(TaxonStatus).filter_by(description = row['StatePlantStatus']).one_or_none(),
					taxonomic_group = row['TaxonomicGroup'],
					national_priority = str(row['NationalPriorityTaxa']) == '1',
					suppress_spatial_representativeness = str(row.get('SuppressSpatialRep', '0')) == '1'
				)

				groups = row['FunctionalGroup']

				if groups:
					for group_pair in groups.split(","):
						if ":" in group_pair:
							group, subgroup = group_pair.split(":", 1)
						else:
							group, subgroup = group_pair, None
						taxon_groups.append(TaxonGroup(
							taxon_id = taxon.id,
							group_name = group,
							subgroup_name = subgroup
						))

			except:
				print(row)
				raise

			session.add(taxon)
			session.add_all(taxon_groups)

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

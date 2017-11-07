import pyproj
from pyproj import Proj
from nesp.db import T1Survey, T1Sighting, T1Site, Taxon, Source, SourceType, SearchType, Unit, get_session
import nesp.util
import os
import logging
import sys
from datetime import date, datetime
import argparse
from contextlib import contextmanager
import csv
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from shapely.geometry import Point
import time
from geoalchemy2 import shape
from tqdm import tqdm

log = logging.getLogger(__name__)

# Helper to make logging and progress bar work together
class TqdmStream(object):
	def write(self, x):
		tqdm.write(x.strip())
	def flush(self):
		pass

def main():
	logging.captureWarnings(True)
	logging.basicConfig(stream=TqdmStream(), level=logging.DEBUG, format='%(asctime)-15s %(levelname)-8s %(message)s')

	parser = argparse.ArgumentParser(description='Import Type 1 data into NESP database')
	parser.add_argument('-i', dest='filename', type=str, help='data file to import (Excel/CSV)')
	parser.add_argument('-t', action='store_true', dest='test', help='test database connection')
	parser.add_argument('-c', action='store_true', dest='commit', help='commit changes (default is dry-run)')
	args = parser.parse_args()

	if args.filename:
		importer = Importer(args.filename, commit = args.commit)
		importer.ingest_data()
	elif args.test:
		test_db()
	else:
		parser.print_help()

def test_db():
	"""
	Test the db conneciton
	"""
	print "Testing DB Connection"
	print
	session = get_session()
	# list all units
	for u in session.query(Unit).all():
		print "%d: %s" % (u.id, u.description)
	print
	print "DB Connection successful"


class ImportLogger(logging.LoggerAdapter):
	def process(self, msg, kwargs):
		return 'Row %s: %s' % (self.extra['row_index'], msg), kwargs

class ImportError(Exception):
	pass

class Importer:
	def __init__(self, filename, commit = False, logger = log, progress_callback = None):
		self.messages = []
		self.filename = filename
		self.commit = commit
		self.log = logger
		self.progress_callback = progress_callback
		# see check_survey_consistency
		self.survey_fields_by_pk = {}

		# count errors/warnings
		self.log_counter = nesp.util.CounterHandler()
		self.log.addHandler(self.log_counter)
		self.error_count = 0
		self.warning_count = 0
		self.processed_rows = 0

	def progress_wrapper(self, iterable):
		# Show a progress bar only if we are running as a script
		if __name__ == '__main__':
			return tqdm(iterable, total = self.row_count)
		else:
			return iterable

	def ingest_data(self):
		"""
		This method reads a csv file, and parse it to ingest_row to process each row
		"""

		self.log.info("Starting import")

		session = get_session()

		# check the extension of the to determine what file it is
		extension = os.path.splitext(self.filename)[1]

		try:
			if extension.lower() in ('.xls', '.xlsx'):
				#excel file
				wb = openpyxl.load_workbook(self.filename)
				for name in wb.get_sheet_names():
					# Skip any worksheets with 'template' in the name
					if "template" in name.lower():
						continue

					self.row_count = len(wb[name].rows)

					for i, row in wb[name].rows:
						row = [cell.value for cell in row]
						if i == 0:
							headers = row
							self.check_headers(row)
						else:
							self.process_row(session, dict(zip(headers, row)), i + 1)

			else:
				#assume it is csv file

				# Count rows first - this is used so we can track progress
				with open(self.filename, "r") as csvfile:
					reader = csv.DictReader(csvfile)
					self.row_count = sum(1 for row in reader)

				with open(self.filename, "r") as csvfile:
					reader = csv.DictReader(csvfile)
					self.check_headers(reader.fieldnames)
					for i, row in enumerate(self.progress_wrapper(reader)):
						self.process_row(session, row, i + 1)

		except ImportError as e:
			self.log.error(str(e))
			self.log.info("Aborting import - no changes will be committed to the database")
			session.rollback()

		else:
			if self.commit:
				self.log.info("Committing changes")
				session.commit()
			else:
				self.log.info("Not committing changes - dry run only")
				session.rollback()

		self.update_log_counts()

		self.log.info("Processed %s/%s rows" % (self.processed_rows, self.row_count))
		self.log.info("Import processing complete. Errors: %s, Warnings: %s" % (self.error_count, self.warning_count))

	def update_log_counts(self):
		self.error_count = self.log_counter.count('ERROR')
		self.warning_count = self.log_counter.count('WARNING')

	def check_headers(self, headers):
		required_headers = set([
			"SourceType",
			"SourceDesc",
			"SourceProvider",
			"SiteName",
			"SearchTypeDesc",
			"SourcePrimaryKey",
			"StartDate",
			"FinishDate",
			"StartTime",
			"FinishTime",
			"DurationInMinutes",
			"AreaInM2",
			"LengthInKm",
			"LocationName",
			"Y",
			"X",
			"ProjectionReference",
			"PositionalAccuracyInM",
			"SpNo",
			"TaxonID",
			"Breeding",
			"Count",
			"UnitID",
			"SurveyComments",
			"SightingComments",
		])

		missing_headers = required_headers - set(headers)

		if len(missing_headers) > 0:
			raise ImportError("Missing required header(s): %s" % ', '.join(missing_headers))

		unrecognized_headers = set(headers) - required_headers

		if len(unrecognized_headers) > 0:
			self.log.warning("Unrecognized column(s) - will be ignored: %s" % ', '.join(unrecognized_headers))

	def process_row(self, session, row, row_index):
		# Each row gets added inside a nested transaction so if anything goes wrong we can rollback just that row
		session.begin_nested()
		try:
			# Disable autoflush - it's a pain
			with session.no_autoflush:
				if self.ingest_row(session, row, row_index):
					session.commit()
				else:
					# If anything went wrong, rollback
					session.rollback()

		except:
			session.rollback()
			self.log.exception("Fatal error during import")
			raise ImportError("Unexpected error - probably a bug (see above)")

		finally:
			self.update_log_counts()
			if self.progress_callback:
				self.progress_callback(row_index, self.row_count)

			self.processed_rows += 1

		if self.processed_rows > 100 and self.error_count + self.warning_count > self.processed_rows / 5:
			raise ImportError("Warning/error rate too high")
		elif self.error_count + self.warning_count > 1000:
			raise ImportError("Too many errors/warnings")

	def ingest_row(self, session, row, row_index):
		"""
		This function ingests data one row at a time. Each row is a dictionary

		See check_headers() for a list of field names
		"""

		# Include row number in all log messages
		log = ImportLogger(self.log, { 'row_index': row_index })

		log.debug("Ingesting: %s" % row.values())

		# If this is set to false, we don't insert the row
		ok = True

		# Helper to avoid repetition when checking fields and logging errors
		@contextmanager
		def field(key):
			try:
				yield row.get(key)
			except ValueError as e:
				log.error('%s: [%s] %s' % (key, row.get(key), str(e)))
				ok = False

		# Strip leading/trailing whitespace from all values, and convert empty strings to None
		for key in row:
			if type(row[key]) in (str, unicode):
				row[key] = row[key].strip()
			if row[key] == '':
				row[key] = None

		# Check that survey information doesn't change for the same SourcePrimaryKey, which would suggest either data
		# corruption or a misunderstanding of how the format works
		try:
			self.check_survey_consistency(row)
		except ValueError as e:
			log.error(str(e))
			self.commit = False # serious error
			ok = False

		# Check for empty values
		for key in ['SearchTypeDesc', 'SourceDesc', 'SiteName', 'TaxonID', 'Count', 'StartDate', 'SpNo', 'X', 'Y', 'UnitID', 'SourcePrimaryKey']:
			if row.get(key) == None:
				log.error("%s: must not be empty" % key)
				return False

		# Source
		source = session.query(Source).filter_by(description = row.get('SourceDesc')).one_or_none()
		if source == None:
			source = Source(
				description = row.get('SourceDesc'),
				provider = row.get('SourceProvider'),
				source_type = get_or_create(session, SourceType, description = row.get('SourceType')))
			session.add(source)
			session.flush()
		else:
			if source.source_type.description != row.get('SourceType'):
				log.error("SourceType: doesn't match database for this source")
				ok = False
			if source.provider != row.get('SourceProvider'):
				log.error("SourceProvider: doesn't match database for this source")
				ok = False

		# SearchType
		search_type = get_or_create(session, SearchType, description = row.get('SearchTypeDesc'))

		# Site
		try:
			site = get_or_create(session, T1Site,
				name = row.get('SiteName'),
				search_type = search_type,
				source = source)
		except MultipleResultsFound:
			log.error("Found duplicate sites in DB - this must be fixed before import can continue")
			self.commit = False # serious error
			return False

		# Survey
		survey = session.query(T1Survey).filter_by(source_primary_key = row.get('SourcePrimaryKey')).one_or_none()
		if survey == None:
			survey = T1Survey(site = site, source_primary_key = row.get('SourcePrimaryKey'))

		survey.site = site
		survey.source = source


		# Start/Finish date/time
		with field('StartDate') as value:
			survey.start_d, survey.start_m, survey.start_y = parse_date(value)

		with field('FinishDate') as value:
			survey.finish_d, survey.finish_m, survey.finish_y = parse_date(value)

		with field('StartTime') as value:
			survey.start_time = parse_time(value)

		with field('FinishTime') as value:
			survey.finish_time = parse_time(value)

		if row.get('FinishDate') and (survey.start_y, survey.start_m, survey.start_d) > (survey.finish_y, survey.finish_m, survey.finish_d):
			log.error("Start date after finish date: %s > %s" % ((survey.start_y, survey.start_m, survey.start_d), (survey.finish_y, survey.finish_m, survey.finish_d)));
			ok = False

		# Duration, area, length, location, accuracy

		with field('Duration') as value:
			survey.duration_in_minutes = validate(value, validate_int, validate_greater_than(0))

		with field('AreaInm2') as value:
			survey.area_in_m2 = validate(value, validate_float, validate_greater_than(0))

		with field('LengthInKm') as value:
			survey.length_in_km = validate(value, validate_float, validate_greater_than(0))

		with field('PositionalAccuracy') as value:
			survey.positional_accuracy_in_m = validate(value, validate_int, validate_greater_than(0))

		survey.location = row.get('Location name')

		# Coordinates
		with field('X') as value:
			x = validate(value, validate_float)

		with field('Y') as value:
			y = validate(value, validate_float)

		if x != None and y != None:
			if x == 0 or y == 0:
				log.warning('Suspicious zero coordinate before projection: %s, %s' % x, y)

			coords = create_point(x, y, row.get('ProjectionReference'))

			survey.coords = shape.from_shape(coords)

			x, y = coords.x, coords.y

			if x < -180 or x > 180 or y < -90 or y > 90:
				log.error('Invalid coordinates after projection: %s, %s' % x, y)
				ok = False
			elif x == 0 or y == 0:
				log.warning('Suspicious zero coordinate after projection: %s, %s' % x, y)

		# Save survey
		session.add(survey)
		session.flush()

		# Taxon
		try:
			taxon = session.query(Taxon).filter_by(id = row.get('TaxonID'), spno = row.get('SpNo')).one()
		except NoResultFound:
			log.error("Invalid TaxonID/Spno: %s, %s" % (row.get('TaxonID'), row.get('SpNo')))
			return False

		sighting = session.query(T1Sighting).filter_by(survey = survey, taxon = taxon).one_or_none()
		if sighting == None:
			sighting = T1Sighting(survey = survey, taxon = taxon)
			session.add(sighting)

		# TODO - breeding - what are we doing with that field?

		with field('Count') as value:
			if value is None:
				sighting.count = 0
			else:
				sighting.count = validate(value, validate_float, validate_greater_than_or_equal(0))

		# Unit
		with field('UnitID') as value:
			unit_id = validate(value, validate_int)
			try:
				sighting.unit = session.query(Unit).get(unit_id)
			except NoResultFound:
				raise ValueError('Unrecognized ID')

		return ok


	def check_survey_consistency(self, row):
		# Check that survey details don't change for the same 'SourcePrimaryKey'
		survey_keys = ['SourceType', 'SourceDesc', 'SourceProvider', 'SiteName', 'SearchTypeDesc', 'StartDate', 'FinishDate', 'StartTime', 'FinishTime', 'Duration', 'AreaInm2', 'LengthInKm', 'LocationName', 'Y', 'X', 'ProjectionReference', 'PositionalAccuracy']
		fields = {key:row.get(key) for key in survey_keys if key in row}
		primary_key = row.get('SourcePrimaryKey')

		if primary_key not in self.survey_fields_by_pk:
			self.survey_fields_by_pk[primary_key] = fields
		elif self.survey_fields_by_pk[primary_key] != fields:

			# Find the fields that are different and log them:
			a, b = self.survey_fields_by_pk[primary_key], fields
			a_diff = { k: a[k] for k in a if a[k] != b.get(k) }
			b_diff = { k: b[k] for k in b if b[k] != a.get(k) }

			raise ValueError("Survey fields do not match for the same SourcePrimaryKey (%s):\n%s\n%s" % (primary_key, a_diff, b_diff))

def create_point(x, y, projection_ref):
	"""
	This function converts x,y value belong to different projectionsystem and datum to a point in WSG84
	Example of projection ref:
	None, EPSG:1234, all of these references are from spatialreference.org
	"""
	if projection_ref not in (None, 'EPSG:4326'):
		p1 = Proj(init=projection_ref)
		p2 = Proj(init='EPSG:4326')
		x, y = pyproj.transform(p1, p2, x, y)

	return Point(x, y)


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
		session.flush()
		return instance

# ----- Validation helpers ------
#
# Use like this:
#
# checked_value = validate(raw_value, validate_int, validate_greater_than(10))
#
# Validator raise ValueErrors as appropriate
# None values are passed through without validation, and a validator can also return None to 
#

def validate(value, *validators):
	for validator in validators:
		if value != None:
			value = validator(value)
	return value

def validate_int(x):
	try:
		return int(x)
	except ValueError:
		raise ValueError('must be an integer')

def validate_float(x):
	try:
		return float(x)
	except ValueError:
		raise ValueError('must be a floating point number')

def validate_greater_than(y):
	return validate_condition(lambda x: x > y, 'must be greater than %s' % y)

def validate_greater_than_or_equal(y):
	return validate_condition(lambda x: x >= y, 'must be greater than or equal to %s' % y)

def validate_condition(fn, message):
	def v(x):
		if fn(x):
			return x
		else:
			raise ValueError(message)
	return v

# ----- End Validation Helpers -----

def parse_date(raw_date):
	"""
	Parses date in DD/MM/YYYY format

	Returns a tuple of the form:
		day, month, year

	If DD = 0 and MM = 0, returns
		None, None, year

	If DD = 0, returns:
		None, month, year

	If raw_date is a datetime object, retrieves the day, month, year from that object

	If raw_date is None or empty, returns:
		None, None, None

	All other cases raise a ValueError
	"""
	if raw_date == None:
		return None, None, None

	if type(raw_date) == datetime:
		return raw_date.day, raw_date.month, raw_date.year

	if type(raw_date) in (str, unicode):
		parts = raw_date.split('/')
		if len(parts) != 3:
			raise ValueError("Invalid date format (expected DD/MM/YYYY)")

		try:
			d, m, y = [int(item) for item in parts]
		except ValueError:
			raise ValueError("Invalid date format (expected DD/MM/YYYY)")

		if y < 1900 or y > date.today().year:
			raise ValueError("Invalid year: %s" % y)
		if m == 0 and d == 0:
			return None, None, y
		if m < 1 or m > 12:
			raise ValueError("Invalid month: %s" % m)
		if d == 0:
			return None, m, y

		# Will raise an error if date is not valid
		date(y, m, d)

		return d, m, y

	raise ValueError("Unable to process date: %s" % raw_date)

def parse_time(raw_time):
	"""
	Parses a time in HH:MM:SS format

	Returns a time object

	If raw_time is already a time object, it is returned as-is

	If raw_time is None or empty, returns None
	"""
	if raw_time == None:
		return None

	if type(raw_time) == time:
		return raw_time

	if type(raw_time) in (str, unicode):
		return datetime.strptime(raw_time, '%H:%M:%S').time()

	raise ValueError("Unable to process time: %s" % raw_time)

if __name__ == '__main__':
	main()

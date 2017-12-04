import csv
import StringIO
from flask import make_response, g, jsonify, Blueprint
from nesp.api.util import csv_response
from nesp.api.util import db_session

bp = Blueprint('lpi_data', __name__)

@bp.route('/lpi-data', methods = ['GET'])
def lpi_data():
	"""Output aggregated data in LPI wide format"""

	output_format = request.args.get('format')
	data = get_data(session)

	if output_format == None or output_format == 'json':
		return jsonify(data)
	elif output_format == "csv":
		header = data[0].keys()
		rows = [[row[x] for x in header] for row in data]
		return csv_response(header + rows)
	else:
		return jsonify("Unsupported format (Supported: csv, json)"), 400


def get_data():
	sql = """
		SELECT
		FROM t1_yearly_aggregation, taxon
		WHERE t1_yearly_aggregation.taxon_id = taxon.id
		GROUP BY SearchTypeID, TaxonID, subibra_id, subibra_name
		"""

	sql_result = db_session.execute(sql)
	result = []

	for row in sql_result.fetch_all():
		item = dict(zip(row, sql_result.keys()))
		for year in range(1950, datetime.now().year+1):
			item[year] = None

		for pair in item['Counts'].split(','):
			(year, count) = pair.split('=')
			item[int(year)] = count

		del item['Counts']

	return result


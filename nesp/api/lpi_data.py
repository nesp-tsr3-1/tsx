import csv
import StringIO
from flask import make_response, g, jsonify, Blueprint
from nesp.api.util import csv_response
from nesp.db import get_session
from datetime import datetime

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
		    replace(taxon.common_name, " ", "_") as Binomial,
		    taxon.spno AS SpNo,
		    taxon.id AS TaxonID,
		    taxon.family_common_name AS FamilyCommonName,
		    taxon.family_scientific_name as FamilyScientificName,
		    taxon.scientific_name as TaxonScientificName, 
		    taxon.population as Population,
		    taxon.order as `Order`,
		    source_type_desc.sourcetype as SourceType,
		    source_type_desc.description as SourceDesc,
		    unit.description as Unit,
		    search_type.description AS SearchTypeDesc,
		    aggregation.subibra_id as subIBRA_name, 
		    aggregation.subibra_name as subIBRA_ID, 
		    GROUP_CONCAT(CONCAT(start_date_y, '=', aggregation.count) ORDER BY start_date_y) AS Counts
		FROM 
		    t1_yearly_aggregation aggregation
		INNER JOIN taxon ON taxon.id = aggregation.taxon_id
		INNER JOIN search_type ON search_type.id = aggregation.search_type_id
		INNER JOIN
		(
		    SELECT source.*, source_type.description as sourcetype FROM `source` 
		    INNER JOIN source_type where source.source_type_id = source_type.id
		) as source_type_desc ON source_type_desc.id = aggregation.source_id
		INNER JOIN unit ON unit.id = aggregation.unit_id
		GROUP BY Binomial, SpNo, TaxonID, SourceType, Unit, SearchTypeDesc, SourceDesc, subIBRA_ID, subIBRA_name
		"""
    session = get_session()
	sql_result = session.execute(sql)
	result = []

	for row in sql_result.fetchall():
		item = dict(zip(row, sql_result.keys()))
		for year in range(1950, datetime.now().year+1):
			item[year] = None

		for pair in item['Counts'].split(','):
			(year, count) = pair.split('=')
			item[int(year)] = count

		del item['Counts']
		result.append(item)

	return result


from fpdf import FPDF
from fpdf.fonts import FontFace
from tsx.api.custodian_feedback_shared import get_form_json_raw, field_options, form_fields
from tsx.api.util import server_timezone
import json
from datetime import datetime
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import os
from tsx.api.util import db_session
from sqlalchemy import text
from tsx.config import data_dir
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import importlib
from datetime import datetime

# These lines are necessary to stop MatplotLib from trying to initialize
# GUI backend and crashing due to not being on the main thread:
import matplotlib
matplotlib.use('agg')

# Using a built-in PDF font for now
font_name='helvetica'

class PDF(FPDF):
	def __init__(self, report_status):
		super().__init__()
		self.generated_at = datetime.now().astimezone(server_timezone()).strftime('%a %d %b %Y, %I:%M%p %Z')
		self.report_status = report_status

	def header(self):
		self.set_fill_color(tsx_green)
		self.rect(x=0, y=0, w=self.w, h=25, style="F")
		self.set_fill_color(white)
		self.set_draw_color(white)
		self.image(tsx_logo_svg, h=12)
		with self.local_context():
			self.set_font(font_name, size=7)
			self.set_text_color(white)
			self.set_y(12)
			self.cell(text="Generated: %s" % self.generated_at, align='R', w=self.epw, new_y="NEXT", new_x="LEFT", h=5)
			self.cell(text="Status: %s" % self.report_status, align='R', w=self.epw)
		self.set_y(35)

	def footer(self):
		self.reset_margin()
		self.set_y(-30)
		self.set_font(font_name, size=7, style="B")
		self.set_text_color(tsx_green)
		self.set_fill_color(white) # This is needed for text color to be correct, don't know why
		self.cell(text="www.tsx.org.au", new_y="NEXT", new_x="LEFT", h=5)
		self.set_font(font_name, size=7)
		self.cell(text="E tsx@uq.edu.au | @AusTSX | The University of Queensland, Long Pocket Precinct, Level 5 Foxtail Bld #1019 | 80 Meiers Rd, Indooroopilly QLD 4068 Australia", new_x="LEFT")
		self.set_fill_color("#F2F2F2")
		self.rect(x=0, y=self.h-20, w=self.w, h=20, style="F")
		self.set_fill_color("#000000")
		self.rect(x=0, y=self.h-2.5, w=self.w, h=2.5, style="F")
		self.set_y(-20)
		self.image(footer_png, w=self.epw)

	def h1(self, text):
		self.set_font(font_name, size=14, style="B")
		self.set_text_color(tsx_green)
		self.write(text=text)
		self.ln(h=8)

	def title_text(self, text):
		self.set_font(font_name, size=14)
		self.set_text_color("#000000")
		self.write(text=text)
		self.ln(h=8)

	def h2(self, text):
		self.set_font(font_name, size=12, style="B")
		self.set_text_color("#000000")
		self.write(text=text)
		self.ln(h=8)

	def h3(self, text):
		self.set_font(font_name, size=10, style="B")
		self.set_text_color("#000000")
		self.write(text=text, h=5)
		self.ln()

	def body(self, text):
		self.set_font(font_name, size=10)
		self.set_text_color("#000000")
		self.write(text=text, h=5)

	def reset_margin(self):
		self.set_margins(15, 10)

def multiple_choice_options(pdf, options, selected_option=None):
	pdf.set_fill_color(tsx_green)
	pdf.set_draw_color("#000000")
	for option in options:
		pdf.set_y(pdf.get_y() + 1)
		if option['id'] == selected_option:
			style = "DF"
		else:
			style = "D"
		pdf.circle(x=pdf.get_x()+1, y=pdf.get_y()+0.5, r=3.5, style=style)
		pdf.set_x(pdf.get_x() + 6)
		pdf.body(option['description'])
		pdf.ln()
	pdf.ln()

def text_in_box(pdf, text):
	with pdf.local_context():
		pdf.set_fill_color("#EEEEEE")
		pdf.set_font(font_name, size=10)
		pdf.multi_cell(
			w=pdf.epw,
			h=5,
			text=text,
			align='L',
			fill=True,
			border=1,
			new_x="LMARGIN",
			padding=2)

def numbered_question(pdf, number, text):
	pdf.set_margins(15, 10)
	pdf.set_font(font_name, size=10, style="B")
	number_text = "%s." % str(number)
	pdf.write(text=number_text, h=5)
	pdf.set_x(22)
	pdf.set_margins(22, 10)
	pdf.write(text=text, h=5)
	pdf.ln(h=5)

def citation(form):
	def fix(s):
		if s is None:
			return None
		else:
			return s.strip().rstrip('.')

	authors = fix(form['source']['authors']) or '<Author(s)>'
	details = fix(form['source']['details']) or '<Data Details>'
	provider = fix(form['source']['provider']) or '<Data Provider>'
	year = str(datetime.now().year)

	return "%s (%s). %s. %s. Aggregated for the Australian Threatened Species Index, an output of the NESP Threatened Species Recovery Hub and operated by the Terrestrial Ecosystem Research Network, The University of Queensland." % (
		authors, year, details, provider)

def avoid_break(pdf):
	with pdf.offset_rendering() as dummy:
		yield dummy
	if dummy.page_break_triggered:
		pdf.add_page()
	yield pdf

def generate_pdf(form_id):
	form = json.loads(get_form_json_raw(form_id))

	pdf = PDF(form['feedback_status']['code'].capitalize())
	pdf.set_title("TSX Custodian Feedback Form %s" % form_id)
	pdf.set_auto_page_break(True, 40)
	pdf.reset_margin()
	pdf.add_page()
	pdf.set_font(font_name, size=12)
	pdf.h1("Custodian Feedback Form")
	pdf.set_font(font_name, size=14)
	pdf.title_text(form['taxon']['scientific_name'] + " (" + form['dataset_id'] + ")")
	pdf.ln()
	pdf.h2("Data citation and monitoring aims")
	pdf.h3("Data Citation")
	pdf.body(citation(form))
	pdf.ln()
	pdf.ln()
	numbered_question(pdf, 1, "Do you agree with the above suggested citation for your data? If no, please indicate how to correctly cite your data.")
	multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('citation_agree'))

	if form['answers'].get('citation_agree') == 'no':
		text_in_box(pdf, form['answers'].get('citation_agree_comments', ''))
		pdf.ln()

	numbered_question(pdf, 2, "Has your monitoring program been explicitly designed to detect population trends over time? If no / unsure, please indicate the aims of your monitoring.")
	multiple_choice_options(pdf, field_options['yes_no_unsure'], form['answers'].get('monitoring_for_trend'))

	numbered_question(pdf, 3, "Do you analyse your own data for trends?")
	multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('analyse_own_trends'))

	numbered_question(pdf, 4, "Can you estimate what percentage (%) of your species' population existed in Australia at the start of your monitoring (assuming this was 100% in 1750)? This information is to help understand population baselines and determine whether the majority of a species' decline may have occurred prior to monitoring.")
	pdf.ln()
	text_in_box(pdf, str(form['answers'].get('pop_1750', '')))
	pdf.ln()

	pdf.add_page()

	pdf.h2("Data summary and processing")

	pdf.set_fill_color("#000000")
	pdf.set_draw_color("#000000")

	# ------ Begin columns ------

	y = pdf.get_y()
	maxy = 0

	# Left column
	pdf.set_left_margin(15)
	pdf.set_right_margin(pdf.w / 2 + 5)

	consitency_plot_data = form['stats']['monitoring_consistency']
	svg = consistency_plot_svg(consitency_plot_data)
	pdf.image(svg, w=pdf.epw)
	pdf.ln()

	pdf.set_font(font_name, size=8, style='I')
	pdf.set_text_color("#000000")
	pdf.write(text="The above dot plot shows the distribution of surveys at unique sites. Each row represents a time series in the dataset or data subset where a species/subspecies was monitored with a consistent method and unit of measurement at a single site over time. The maximum number of time-series included in this plot is 50.", h=4)

	maxy = max(maxy, pdf.get_y())

	# Right column
	pdf.set_y(y)
	pdf.set_left_margin(pdf.w / 2 + 5)
	pdf.set_right_margin(15)
	pdf.set_x(pdf.w / 2 + 5)

	png = intensity_map_png(form['stats']['intensity_map'])
	pdf.image(png, w=pdf.epw)
	pdf.ln()

	pdf.set_font(font_name, size=8, style='I')
	pdf.set_text_color("#000000")
	pdf.write(text="The above map shows the location of your monitoring sites.", h=4)

	maxy = max(maxy, pdf.get_y())

	pdf.reset_margin()
	pdf.set_y(maxy)
	pdf.ln()
	pdf.ln()

	# ------ End columns ------

	pdf.set_fill_color(white)
	headings_style = FontFace(emphasis="BOLD", fill_color='#EEEEEE')
	bold_style = FontFace(emphasis="BOLD")
	pdf.set_font(font_name, size=8)
	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		headings_style=headings_style,
		col_widths=(3,3,2,2,2)
		) as table:
		headings = table.row()
		headings.cell('Search Type Description (monitoring method)')
		headings.cell('Unit of Measurement')
		headings.cell('Unit Type')
		headings.cell('Data Processing Type')
		headings.cell('Method of Aggregation')

		for item in form['stats']['processing_summary']:
			row = table.row()
			row.cell(item['search_type'])
			row.cell(item['unit'])
			row.cell(item['unit_type'])
			row.cell(item['data_processing_type'])
			row.cell(item['aggregation_method'])

	pdf.ln()

	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		headings_style=headings_style,
		col_widths=(3,7,2)
		) as table:
		headings = table.row()
		headings.cell('Management Category')
		headings.cell('Management Comments')
		headings.cell('Number of Sites')

		for item in form['stats']['site_management_summary']:
			row = table.row()
			row.cell(item['management_category'])
			row.cell(item['management_comments'])
			row.cell(str(item['site_count']))

	pdf.ln()
	pdf.ln()

	numbered_question(pdf, 5, "Are the above values representative of your datasets?")
	multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('data_summary_agree'))
	if form['answers'].get('data_summary_agree') == 'no':
		text_in_box(pdf, str(form['answers'].get('data_summary_agree_comments', '')))
		pdf.ln()


	# Proof of concept of code to avoid page-breaks within a section
	# (pdf.unbreakable() doesn't work with get_y())
	for doc in avoid_break(pdf):
		numbered_question(doc, 6, "Do you agree with how your data were handled? If no, please suggest an alternative method of aggregation.")
		multiple_choice_options(doc, field_options['yes_no'], form['answers'].get('processing_agree'))
		if form['answers'].get('processing_agree') == 'no':
			text_in_box(doc, str(form['answers'].get('processing_agree_comments', '')))
			doc.ln()

	# ------- Statistics and trend estimate --------

	pdf.h2("Statistics and trend estimate")
	pdf.set_fill_color(white)
	pdf.set_font(font_name, size=8)

	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		headings_style=headings_style,
		col_widths=(10,2)
		) as table:
		headings = table.row()
		headings.cell('Statistics (units)')
		headings.cell('Mean (±SD)')

		row = table.row()
		with pdf.local_context():
			pdf.set_font(font_name, size=8, style='B')
			row.cell("Raw data", colspan=2)

		stats = form['stats']['raw_data_stats']
		row_data = [
			('Period of monitoring (years)',
				'%s-%s' % (stats['min_year'], stats['max_year'])),
			('Number of data points (surveys)',
				format_int(stats['survey_count'])),
			('Range of raw data (counts)',
				'%s-%s' % (format_int(stats['min_count']), format_int(stats['max_count']))),
			('Number of 0 counts',
				format_int(stats['zero_counts']))
		]

		for name, value in row_data:
			row = table.row()
			row.cell(name)
			row.cell(value)

		row = table.row()
		with pdf.local_context():
			pdf.set_font(font_name, size=8, style='B')
			row.cell("Aggregated data", colspan=2)

		stats = form['stats']['time_series_stats']
		row_data = [
			('Number of repeatedly monitored sites (time series)',
				format_int(stats['time_series_count'])),
			('Time-series length (years)',
				"%s (±%s)" % (format_decimal(stats['time_series_length_mean']), format_decimal(stats['time_series_length_std']))),
			('Time-series sample years (years)',
				"%s (±%s)" % (format_decimal(stats['time_series_sample_years_mean']), format_decimal(stats['time_series_sample_years_std']))),
			('Time-series completeness (%)',
				"%s (±%s)" % (format_decimal(stats['time_series_completeness_mean']), format_decimal(stats['time_series_completeness_std']))),
			('Time series sampling evenness (0 = very even sampling)',
				"%s (±%s)" % (format_decimal(stats['time_series_sampling_evenness_mean']), format_decimal(stats['time_series_sampling_evenness_std'])))
		]

		for name, value in row_data:
			row = table.row()
			row.cell(name)
			row.cell(value)

	pdf.ln()
	pdf.ln()

	numbered_question(pdf, 7, "Do the above statistics appear representative of your dataset?")
	multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('statistics_agree'))
	if form['answers'].get('statistics_agree') == 'no':
		text_in_box(pdf, str(form['answers'].get('statistics_agree_comments', '')))
		pdf.ln()

	pdf.ln()

	pdf.set_fill_color("#000000")
	pdf.set_draw_color("#000000")
	trend_plot_data = form['stats']['trend']
	svg = trend_plot_svg(trend_plot_data)
	pdf.image(svg, w=pdf.epw)
	pdf.ln()

	pdf.set_font(font_name, size=8, style='I')
	pdf.set_text_color("#000000")
	pdf.write(text="The above graph shows the estimated yearly change in relative abundance in relation to a baseline year where the index is set to 1. Changes are proportional - a value of 0.5 indicates the population is 50% below the baseline value; a value of 1.5 indicates 50% above baseline. The overall trend (mean value per year) is shown by the blue line - this line is used in the final multi-species TSX. The grey cloud indicates the uncertainty in the estimate as measured by the variability between all-time series in your dataset.", h=4)

	pdf.ln()
	pdf.ln()

	numbered_question(pdf, 8, "Do you agree with the trend estimate? If no or unsure, please elaborate (include detail on trends for specific sites where relevant).")
	multiple_choice_options(pdf, field_options['yes_no_unsure'], form['answers'].get('trend_agree'))
	if form['answers'].get('trend_agree') == 'no' or form['answers'].get('trend_agree') == 'unsure':
		text_in_box(pdf, str(form['answers'].get('trend_agree_comments', '')))
		pdf.ln()

	numbered_question(pdf, 9, "Looking at the trend for your data, what should be the reference year at which the index should start?")
	pdf.ln()
	text_in_box(pdf, str(form['answers'].get('start_year', '')))
	pdf.ln()

	numbered_question(pdf, 10, "Looking at the trend for your data, what should be the year at which the index should end?")
	pdf.ln()
	text_in_box(pdf, str(form['answers'].get('end_year', '')))
	pdf.ln()

	pdf.add_page()

	# ------------ Data Suitability ------------
	pdf.ln()
	pdf.h2("Data Suitablility")


	pdf.set_fill_color(white)
	pdf.set_font(font_name, size=8)

	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		headings_style=headings_style,
		col_widths=(3, 3, 1, 1, 4)
		) as table:
		headings = table.row()
		headings.cell('Suitablility criteria')
		headings.cell('Description')
		headings.cell('Your assessment', colspan=3)

		form_fields_by_name = { f.name: f for f in form_fields }
		selected_style = FontFace(fill_color=tsx_green)

		for number, field_name, title, description in [
			(11, 'standardisation_of_method_effort', 'Standardisation of method effort', 'This data suitability indicator rates the degree of standardisation of monitoring method/effort and is assessed to the data source level by enquiring with the data custodian and examining data.'),
			(12, 'objective_of_monitoring', 'Objective of monitoring', 'This field indicates the objective of the monitoring.'),
			(13, 'consistency_of_monitoring', 'Consistency of monitoring', 'This data suitability indicator rates the degree of consistency by which the same sites were repeatedly monitored over time.'),
			(14, 'monitoring_frequency_and_timing', 'Monitoring frequency and timing', 'This data suitability indicator rates whether the taxon was monitored with an appropriate frequency and during an appropriate season/timing.'),
			(15, 'absences_recorded', 'Were absences recorded systematically?', 'Absences are non-detections of taxa i.e. where 0 counts of a species are recorded.')]:

			field = form_fields_by_name[field_name]
			options = field_options[field_name]

			for index, option in enumerate(options):
				row = table.row()
				if index == 0:
					row.cell("%d. %s" % (number, title), rowspan = len(options), v_align='T', style=bold_style)
					row.cell(description, rowspan = len(options), v_align='T')

				selected = str(option['id']) == form['answers'].get(field_name)
				if selected:
					row.cell("", style=selected_style)
				else:
					row.cell("")

				# row.cell("%s" % selected)
				row.cell(str(option['id']))
				row.cell(str(option['description']).encode('ascii', 'ignore').decode('ascii'))

	pdf.ln()

	pdf.set_font(font_name, size=10, style="B")
	pdf.write(text="Please add any additional comments on data suitability and the criteria below.")
	pdf.ln()
	pdf.ln()
	text_in_box(pdf, str(form['answers'].get('data_suitability_comments', '')))
	pdf.ln()

	pdf.ln()
	pdf.h2("Monitoring program funding, logistics and governance")
	pdf.ln()

	numbered_question(pdf, 16, "Please indicate if you would prefer to provide this information via a phone or video call with our project team:")
	multiple_choice_options(pdf, field_options['monitoring_program_information_provided'], form['answers'].get('monitoring_program_information_provided'))


	if(form['answers'].get('monitoring_program_information_provided') in ['provided', 'provided_copy']):
		numbered_question(pdf, 17, "Effort: How much time on average per year was spent on project labour, i.e. data collection in the field?")
		answer_table(pdf, form, [
			('a. Days/year paid labour:', 'effort_labour_paid_days_per_year'),
			('b. Days/year volunteered time:', 'effort_labour_volunteer_days_per_year')])

		numbered_question(pdf, 18, "Effort: How much time on average per year was spent on project overheads, e.g. data collation and dataset maintenance?")
		answer_table(pdf, form, [
			('a. Days/year paid labour:', 'effort_overheads_paid_days_per_year'),
			('b. Days/year volunteered time:', 'effort_overheads_volunteer_days_per_year')])

		numbered_question(pdf, 19, "Effort: Approximately how many people were involved in the last bout of monitoring (including both field and office work)")
		answer_table(pdf, form, [
			('a. Paid staff:', 'effort_paid_staff_count'),
			('b. Volunteers:', 'effort_volunteer_count')])

		numbered_question(pdf, 20, "Funding: How much do you think in AUD$ a single survey costs (not counting in-kind support)?")
		text_in_box(pdf, format_currency(form['answers'].get('funding_cost_per_survey_aud')))
		pdf.ln()

		numbered_question(pdf, 21, "Funding: Can you estimate in AUD$ the total investment in the dataset to date (again not counting in-kind support)?")
		text_in_box(pdf, format_currency(form['answers'].get('funding_total_investment_aud')))
		pdf.ln()

		numbered_question(pdf, 22, "Funding: Who has been paying for the monitoring? (e.g. government grants, research funds, private donations etc. - list multiple funding sources if they have been needed over the years)")
		answer_table(pdf, form, [
			('a. Government grants:', 'funding_source_government_grants'),
			('b. Research funds:', 'funding_source_research_funds'),
			('c. Private donations:', 'funding_source_private_donations'),
			('d. Other:', 'funding_source_other'),
			('e. Can you estimate the total number of funding sources so far?:', 'funding_source_count')])

		pdf.add_page()

		numbered_question(pdf, 23, "Leadership: Who has been providing the drive to keep the monitoring going after the baseline was established?")
		text_in_box(pdf, get_answer(form, 'leadership'))
		pdf.ln()

		numbered_question(pdf, 24, "Impact: Are data being used to directly inform management of the threatened species or measure the effectiveness of management actions?")
		answer_table(pdf, form, [
			('a.', 'impact_used_for_management'),
			('b. Please expand:', 'impact_used_for_management_comments')])

		numbered_question(pdf, 25, "Impact: Is your organisation responsible for managing this species in the monitored area?")
		text_in_box(pdf, get_answer(form, 'impact_organisation_responsible'))
		pdf.ln()

		numbered_question(pdf, 26, "Impact: Can you describe any management that has changed because of the monitoring?")
		text_in_box(pdf, get_answer(form, 'impact_management_changes'))
		pdf.ln()

		numbered_question(pdf, 27, "Data availability: Is your monitoring data readily available to the public (e.g. through reports, or on website). If not, can the public access it?")
		text_in_box(pdf, get_answer(form, 'data_availability'))
		pdf.ln()

		numbered_question(pdf, 28, "Succession: Do you have commitments to extend the monitoring into the future?")
		answer_table(pdf, form, [
			('a.', 'succession_commitment'),
			('b. Please expand:', 'succession_commitment_comments')])

		numbered_question(pdf, 29, "Succession: Have you developed a plan for continual monitoring when the current organisers/you need to stop?")
		answer_table(pdf, form, [
			('a.', 'succession_plan'),
			('b. Please expand:', 'succession_plan_comments')])

		numbered_question(pdf, 30, "Design: Was there thought about the statistical power of the monitoring when it was started (i.e. the probability that change could be detected?)")
		answer_table(pdf, form, [
			('a.', 'design_statistical_power'),
			('b. Please expand:', 'design_statistical_power_comments')])

		pdf.add_page()

		numbered_question(pdf, 31, "Design: Is anything other than the numbers of threatened species being monitored at the same time that could explain changes in abundance (e.g. prevalence of a threat, fire, breeding success, etc?)")
		answer_table(pdf, form, [
			('a.', 'design_other_factors'),
			('b. Please expand:', 'design_other_factors_comments')])

		numbered_question(pdf, 32, "Co-benefits: Is the monitoring program for this species also collecting trend information on other threatened species?")
		answer_table(pdf, form, [
			('a.', 'co_benefits_other_species'),
			('b. Please expand:', 'co_benefits_other_species_comments')])


	return bytes(pdf.output())

def answer_table(pdf, form, rows):
	pdf.set_fill_color(white) # this not always working, presumably a bug if pypdf
	pdf.set_font(font_name, size=8)

	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		col_widths=(4,8),
		first_row_as_headings=False
		) as table:
		for title, field in rows:
			row = table.row()
			row.cell(title)
			row.cell(get_answer(form, field))

	pdf.ln()
	pdf.ln()

def get_answer(form, field):
	return str(form['answers'].get(field, '') or '')

def format_int(x):
	return f'{x:,}'

def format_decimal(x):
	return f'{x:,.2f}'

def format_currency(x):
	if x is None:
		return ''
	return "$" + f'{x:,.02f}'

def consistency_plot_svg(data):
	xys = [(year, i + 1) for i, series in enumerate(data) for year, count in series]
	x, y = zip(*xys)

	fig = plt.figure(figsize=(6, 4.5))
	ax = fig.gca()
	ax.yaxis.get_major_locator().set_params(integer=True)
	plt.xlabel('Year')
	plt.ylabel('Sites (time series)')
	plt.grid(True)
	plt.plot(x, y, 'ko', ms=5)

	svg_data = StringIO()
	fig.savefig(svg_data, format='svg')

	return bytes(svg_data.getvalue(), encoding="utf8")

def trend_plot_svg(data):
	rows = data.split("\n")

	rows = [row for row in rows if len(row) > 0 and "NA" not in row and "LPI" not in row]
	series = list(zip(*[[float(x.strip('"')) for x in row.split(" ")] for row in rows]))

	(years, trend, lower, upper, num_species) = series[0:5]

	years = [int(year) for year in years]

	fig = plt.figure(figsize=(12, 4.5))
	plt.xlabel('Year')
	plt.ylabel('Index (%s = 1)' % years[0])
	plt.grid(True)
	plt.plot(years, trend)
	plt.gca().set_xlim(years[0], years[-1])
	# Note: hatch fill doesn't work because it produces an SVG that PyPDF can't render
	plt.fill_between(years, lower, upper, color="#EEEEEE")

	svg_data = StringIO()
	fig.savefig(svg_data, format='svg')

	return bytes(svg_data.getvalue(), encoding="utf8")

def intensity_map_png(data):
	xs = [p["lon"] for p in data]
	ys = [p["lat"] for p in data]

	map_projection = ccrs.AlbersEqualArea(
		central_longitude=135,
		central_latitude=-25,
		standard_parallels=(-35,-10))

	fig = plt.figure(figsize=(6, 4.5))
	ax = fig.add_subplot(projection=map_projection)
	buffer = 7
	minx = min(min(xs) - buffer, 110)
	maxx = max(max(xs) + buffer, 160)
	miny = min(min(ys) - buffer, -45)
	maxy = max(max(ys) + buffer, -5)

	ax.set_extent([minx, maxx, miny, maxy])
	# ax.add_feature(cfeature.LAND)
	# ax.add_feature(cfeature.OCEAN)
	ax.coastlines()
	gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, color='#00000040')
	gl.top_labels = False
	gl.right_labels = False

	scale = 1.5
	ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#6C85CC40', mew=0,  markersize=10 * scale)
	ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#6C85CC80', mew=0,  markersize=9 * scale)
	ax.plot(xs, ys, marker='o', linewidth=0, transform=ccrs.Geodetic(), mfc='#FD49FB80', mew=0, markersize=7 * scale)

	png_data = BytesIO()
	fig.savefig(png_data, format='png', dpi=180)
	return png_data.getvalue()


white = "#FFFFFF"
tsx_green = "#266F6A"

footer_png = importlib.resources.read_binary("tsx.resources", "pdf-footer.png")
tsx_logo_svg = importlib.resources.read_binary("tsx.resources", "pdf-logo.svg")

# This should be called after forms have had their status changed to 'archived', which
# occurs when the update_custodian_feedback() procedure is called.
# It finds all forms that are archived but do not yet have a 'file_name' attribute.
# For each of these it generates a PDF file and updates the 'file_name' attribute to
# point to the newly created PDF file.
def generate_archive_pdfs(source_id):
	rows = db_session.execute(text("""
		SELECT id FROM custodian_feedback
		WHERE source_id = :source_id
		AND feedback_status_id = (SELECT id FROM feedback_status WHERE code = 'archived')
		AND feedback_type_id = (SELECT id FROM feedback_type WHERE code = 'integrated')
		AND file_name IS NULL
		"""), { 'source_id': source_id })

	for (form_id,) in rows:
		generate_archive_pdf(form_id)

def generate_archive_pdf(form_id):
	form = json.loads(get_form_json_raw(form_id))
	print(form)
	file_name = 'TSX Custodian Feedback %s %s.pdf' % (form['dataset_id'], form['id'])
	path = os.path.join(data_dir("custodian-feedback"), file_name)

	with open(path, mode='wb') as file:
		file.write(generate_pdf(form_id))

	db_session.execute(text("""
		UPDATE custodian_feedback
		SET file_name = :file_name
		WHERE id = :form_id
		"""), { 'file_name': file_name, 'form_id': form_id })
	db_session.commit()


# For testing purposes
if __name__ == '__main__':
	pdf = generate_pdf(1024)
	with open('test.pdf', 'wb') as f:
		f.write(pdf)

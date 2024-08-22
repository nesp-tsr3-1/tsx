from fpdf import FPDF
from fpdf.fonts import FontFace
from tsx.api.custodian_feedback_shared import get_form_json_raw, field_options, form_fields
import json
from datetime import datetime
import matplotlib.pyplot as plt
from io import StringIO

# These lines are necessary to stop MatplotLib from trying to initialize
# GUI backend and crashing due to not being on the main thread:
import matplotlib
matplotlib.use('agg')

# Using a built-in PDF font for now
font_name='helvetica'

class PDF(FPDF):
	def header(self):
		self.set_fill_color(tsx_green)
		self.rect(x=0, y=0, w=self.w, h=25, style="F")
		self.set_fill_color(white)
		self.set_draw_color(white)
		self.image(tsx_logo_svg, h=12)
		self.set_y(35)

	def footer(self):
		self.reset_margin()
		self.set_y(-30)
		self.set_font(font_name, size=7, style="B")
		self.set_text_color(tsx_green)
		self.set_fill_color(white) # This is needed for text color to be correct, don't know why
		self.cell(text="www.tsx.org.au", new_y="NEXT", new_x="LEFT", h=5)
		self.set_font(font_name, size=7)
		self.cell(text="E tsx@uq.edu.au | @AusTSX | The University of Queensland, Long Pocket Precinct, Level 5 Foxtail Bld #1019 | 80 Meiers Rd, Indooroopilly QLD 4068 Australia")
		self.set_fill_color("#F2F2F2")
		self.rect(x=0, y=self.h-20, w=self.w, h=20, style="F")
		self.set_fill_color("#000000")
		self.rect(x=0, y=self.h-2.5, w=self.w, h=2.5, style="F")

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

	pdf = PDF()
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
	# pdf.image(svg, w=pdf.epw)
	pdf.set_fill_color("#EEEEEE")
	rect_h = pdf.epw * 0.7
	pdf.rect(pdf.get_x(), y + 4.5, pdf.epw, rect_h, style="F")
	pdf.set_y(y + rect_h / 2)
	pdf.set_font(font_name, size=8)
	pdf.cell(w=pdf.epw, text="[Map]", align="C")
	pdf.set_y(y + rect_h + 5.5)
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
			row.cell(item['unit'])
			row.cell('')
			row.cell('')

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
	multiple_choice_options(pdf, field_options['cost_data_provided'], form['answers'].get('cost_data_provided'))


	if(form['answers'].get('cost_data_provided') in ['provided', 'provided_copy']):
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

white = "#FFFFFF"
tsx_green = "#266F6A"


tsx_logo_svg = b"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: Adobe Illustrator 25.4.1, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
	 viewBox="0 0 623.62 141.73" style="enable-background:new 0 0 623.62 141.73;" xml:space="preserve">
<g>
	<path class="st0" d="M85.14,22.48c1.39,0,2.14,0.76,2.14,2.27v14.37c0,1.39-0.76,2.14-2.14,2.14H62.08v69.05
		c0,1.51-0.76,2.27-2.14,2.27H44.06c-1.39,0-2.14-0.76-2.14-2.27V41.25H18.86c-1.51,0-2.27-0.76-2.27-2.14V24.75
		c0-1.51,0.76-2.27,2.27-2.27H85.14z"/>
	<path class="st0" d="M127.85,114.09c-12.85,0-22.43-3.78-33.14-12.35c-1.13-0.88-1.26-1.89-0.5-3.02l8.57-12.22
		c0.76-1.01,1.89-1.26,3.02-0.38c7.56,5.29,15.25,8.57,23.44,8.69c8.19,0,13.99-2.77,13.99-8.32c0-6.43-7.56-8.44-16.25-10.21
		c-12.73-2.65-31.63-8.95-31.63-29.36c0-17.51,15-26.08,34.15-26.08c11.09,0,20.04,2.77,30.49,9.7c1.26,0.76,1.51,1.89,0.63,3.02
		l-8.06,12.1c-0.76,1.13-1.89,1.39-3.15,0.63c-6.55-4.16-13.86-6.3-20.92-6.3c-8.95,0-12.48,3.02-12.48,7.56
		c0,5.54,5.29,7.06,16,9.58c17.52,4.28,32.01,10.08,32.01,28.73C164.02,103.5,149.9,114.09,127.85,114.09z"/>
	<path class="st0" d="M244.02,109.93c0.88,1.39,0.25,2.65-1.51,2.65h-18.52c-1.13,0-2.02-0.63-2.52-1.64l-15.25-28.48l-15.12,28.48
		c-0.63,1.01-1.39,1.64-2.65,1.64h-18.52c-1.64,0-2.39-1.26-1.51-2.65l25.2-42.59l-23.19-42.21c-0.88-1.51-0.13-2.65,1.64-2.65
		h17.77c1.13,0,2.02,0.5,2.52,1.64l13.86,28.6l13.86-28.6c0.5-1.13,1.39-1.64,2.52-1.64h17.89c1.64,0,2.39,1.13,1.64,2.65
		l-23.19,42.21L244.02,109.93z"/>
</g>
<g>
	<path class="st0" d="M353.31,23.35c0.24,0,0.43,0.14,0.43,0.38v1.68c0,0.24-0.19,0.38-0.43,0.38h-10.8v31.49
		c0,0.24-0.19,0.38-0.43,0.38h-1.82c-0.24,0-0.43-0.14-0.43-0.38V25.8h-10.71c-0.24,0-0.38-0.14-0.38-0.38v-1.68
		c0-0.24,0.14-0.38,0.38-0.38H353.31z"/>
	<path class="st0" d="M367.32,32.42c6.14,0,10.23,3.12,10.23,10.08v14.79c0,0.24-0.14,0.38-0.38,0.38h-1.73
		c-0.24,0-0.43-0.14-0.43-0.38V42.55c0-5.52-2.78-7.78-7.82-7.78c-2.45,0-4.85,0.62-6.77,1.58v20.93c0,0.24-0.14,0.38-0.38,0.38
		h-1.73c-0.24,0-0.43-0.14-0.43-0.38V23.73c0-0.24,0.19-0.38,0.43-0.38h1.73c0.24,0,0.38,0.14,0.38,0.38v10.27
		C362.47,33.05,364.78,32.42,367.32,32.42z"/>
	<path class="st0" d="M384.74,57.67c-0.24,0-0.43-0.14-0.43-0.38V34.63c0-0.19,0.1-0.38,0.34-0.48c2.35-1.1,5.33-1.73,8.11-1.73
		c1.58,0,3.26,0.19,4.9,0.43c0.29,0.05,0.38,0.19,0.38,0.43v1.49c0,0.24-0.19,0.38-0.43,0.34c-1.44-0.24-3.07-0.38-4.56-0.38
		c-2.21,0-4.46,0.43-6.19,1.15v21.41c0,0.24-0.14,0.38-0.38,0.38H384.74z"/>
	<path class="st0" d="M420.12,46.25c0,0.24-0.19,0.38-0.43,0.38h-16.56v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.74,3.17,9.74,9.31V46.25z M410.38,34.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C417.62,37.18,414.6,34.78,410.38,34.78z"/>
	<path class="st0" d="M434.38,32.42c5.95,0,9.17,3.31,9.17,9.07v14.59c0,0.19-0.1,0.38-0.34,0.48c-2.11,0.82-5.38,1.63-8.93,1.63
		c-5.52,0-10.08-2.59-10.08-7.78c0-4.94,3.89-7.58,10.08-7.58c2.45,0,4.9,0.43,6.72,0.77v-2.06c0-4.27-1.87-6.77-6.72-6.77
		c-2.88,0-5.57,0.86-7.34,1.97c-0.19,0.14-0.38,0.1-0.53-0.1l-0.82-1.25c-0.14-0.19-0.14-0.38,0-0.48
		C427.7,33.43,430.78,32.42,434.38,32.42z M434.28,55.9c2.69,0,5.04-0.58,6.72-1.15v-8.93c-1.78-0.38-4.32-0.72-6.72-0.72
		c-4.99,0-7.49,1.92-7.49,5.33C426.79,53.88,429.91,55.9,434.28,55.9z"/>
	<path class="st0" d="M457.99,55.8c0.62,0,1.73-0.05,2.64-0.1c0.24-0.05,0.38,0.1,0.38,0.38v1.54c0,0.24-0.1,0.38-0.38,0.43
		c-0.86,0.1-2.06,0.14-2.74,0.14c-4.7,0-7.78-2.83-7.78-8.16V27.19c0-0.24,0.14-0.38,0.38-0.38h1.54c0.24,0,0.38,0.14,0.43,0.38
		l0.14,5.86h7.34c0.24,0,0.38,0.19,0.38,0.43v1.49c0,0.24-0.14,0.38-0.38,0.38h-7.3v14.59C452.66,53.59,454.49,55.8,457.99,55.8z"/>
	<path class="st0" d="M483.62,46.25c0,0.24-0.19,0.38-0.43,0.38h-16.56v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.74,3.17,9.74,9.31V46.25z M473.88,34.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C481.13,37.18,478.1,34.78,473.88,34.78z"/>
	<path class="st0" d="M489.86,57.67c-0.24,0-0.43-0.14-0.43-0.38V34.78c0-0.19,0.1-0.38,0.34-0.48c2.64-1.15,5.71-1.87,8.93-1.87
		c6.38,0,10.42,3.17,10.42,9.98v14.88c0,0.24-0.14,0.38-0.38,0.38H507c-0.24,0-0.43-0.14-0.43-0.38V42.5c0-5.38-2.83-7.73-7.87-7.73
		c-2.4,0-4.85,0.48-6.72,1.15v21.36c0,0.24-0.14,0.38-0.38,0.38H489.86z"/>
	<path class="st0" d="M534.69,46.25c0,0.24-0.19,0.38-0.43,0.38H517.7v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.74,3.17,9.74,9.31V46.25z M524.95,34.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C532.2,37.18,529.17,34.78,524.95,34.78z"/>
	<path class="st0" d="M556.77,23.73c0-0.24,0.14-0.38,0.38-0.38h1.73c0.29,0,0.43,0.14,0.43,0.38v32.31c0,0.19-0.1,0.38-0.34,0.43
		c-2.64,1.06-5.86,1.73-8.93,1.73c-6.29,0-10.42-3.17-10.42-10.32V42.7c0-6.77,4.03-10.27,10.23-10.27c2.59,0,4.99,0.77,6.91,1.92
		V23.73z M550.1,55.9c2.4,0,4.8-0.43,6.67-1.1v-18c-1.87-1.25-4.22-2.06-6.72-2.06c-4.99,0-7.82,2.4-7.82,7.97v5.18
		C542.23,53.59,545.11,55.9,550.1,55.9z"/>
	<path class="st0" d="M342.65,113.2c-4.8,0-8.16-1.49-11.91-4.56c-0.19-0.19-0.19-0.38-0.05-0.58l1.01-1.39
		c0.14-0.19,0.34-0.24,0.58-0.1c3.36,2.74,6.48,4.08,10.42,4.13c5.28,0,9.36-2.26,9.36-6.91c0-4.18-3.02-5.86-9.84-7.39
		c-6.67-1.54-11.42-4.18-11.42-9.94c0-5.95,5.42-8.64,11.71-8.64c4.37,0,7.78,1.3,11.18,3.84c0.24,0.14,0.19,0.38,0.1,0.58
		l-0.96,1.34c-0.14,0.24-0.38,0.29-0.58,0.14c-2.98-2.26-6.29-3.36-10.03-3.41c-4.8,0-8.74,2.02-8.74,6.24
		c0,4.08,3.41,5.86,9.36,7.25c7.63,1.82,11.91,4.13,11.91,9.98C354.75,110.08,349.56,113.2,342.65,113.2z"/>
	<path class="st0" d="M369.67,87.42c6.24,0,10.37,3.17,10.37,10.32v5.18c0,6.77-4.03,10.27-10.27,10.27c-2.54,0-4.99-0.77-6.86-1.92
		v10.13c0,0.24-0.14,0.38-0.38,0.38h-1.73c-0.24,0-0.43-0.14-0.43-0.38V89.63c0-0.24,0.1-0.38,0.29-0.48
		C363.34,88.1,366.55,87.42,369.67,87.42z M377.45,102.93v-5.18c0-5.71-2.88-8.02-7.83-8.02c-2.45,0-4.8,0.43-6.72,1.15v17.91
		c1.87,1.3,4.27,2.11,6.72,2.11C374.66,110.9,377.45,108.5,377.45,102.93z"/>
	<path class="st0" d="M404.91,101.25c0,0.24-0.19,0.38-0.43,0.38h-16.56v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.75,3.17,9.75,9.31V101.25z M395.16,89.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C402.41,92.18,399.38,89.78,395.16,89.78z"/>
	<path class="st0" d="M419.74,113.2c-6.14,0-9.84-3.94-9.84-9.07V96.5c0-5.14,3.7-9.07,9.84-9.07c2.88,0,5.38,0.86,7.73,2.5
		c0.24,0.19,0.29,0.38,0.14,0.58l-0.82,1.25c-0.14,0.14-0.34,0.24-0.58,0.1c-2.02-1.39-4.08-2.06-6.48-2.06
		c-4.71,0-7.3,2.93-7.3,6.72v7.63c0,3.84,2.64,6.77,7.3,6.77c2.54,0,4.85-0.82,7.1-2.45c0.24-0.19,0.43-0.14,0.58,0.05l0.82,1.2
		c0.14,0.24,0.14,0.43-0.05,0.58C425.69,112.19,423.05,113.2,419.74,113.2z"/>
	<path class="st0" d="M434.47,82.86c-1.01,0-1.73-0.72-1.73-1.68c0-1.01,0.72-1.73,1.73-1.73c0.96,0,1.68,0.72,1.68,1.73
		C436.15,82.14,435.43,82.86,434.47,82.86z M433.56,112.67c-0.24,0-0.38-0.14-0.38-0.38V88.38c0-0.29,0.14-0.43,0.38-0.43h1.78
		c0.24,0,0.38,0.14,0.38,0.43v23.91c0,0.24-0.14,0.38-0.38,0.38H433.56z"/>
	<path class="st0" d="M461.54,101.25c0,0.24-0.19,0.38-0.43,0.38h-16.56v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.75,3.17,9.75,9.31V101.25z M451.8,89.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C459.05,92.18,456.02,89.78,451.8,89.78z"/>
	<path class="st0" d="M475.17,113.2c-3.46,0-6.58-1.06-9.26-3.12c-0.24-0.14-0.24-0.34-0.14-0.53l0.82-1.34
		c0.14-0.24,0.34-0.29,0.58-0.1c2.4,1.78,5.09,2.78,8.06,2.78c3.94,0,6.72-1.68,6.72-4.8c0-3.41-3.55-4.13-6.72-4.8
		c-3.74-0.72-9.07-2.16-9.07-7.3c0-4.32,4.08-6.58,8.88-6.58c3.31,0,5.9,0.91,8.4,2.3c0.24,0.14,0.29,0.34,0.14,0.58l-0.77,1.3
		c-0.1,0.19-0.34,0.29-0.58,0.14c-2.06-1.2-4.66-1.97-7.3-1.97c-3.74,0-6.29,1.58-6.29,4.22c0,3.31,3.46,4.22,7.06,4.99
		c4.13,0.86,8.83,1.92,8.83,7.01C484.53,110.42,480.93,113.2,475.17,113.2z"/>
	<path class="st0" d="M504.6,112.29c0,0.24-0.14,0.38-0.38,0.38h-1.87c-0.24,0-0.38-0.14-0.38-0.38V78.73
		c0-0.24,0.14-0.38,0.38-0.38h1.87c0.24,0,0.38,0.14,0.38,0.38V112.29z"/>
	<path class="st0" d="M513,112.67c-0.24,0-0.43-0.14-0.43-0.38V89.78c0-0.19,0.1-0.38,0.34-0.48c2.64-1.15,5.71-1.87,8.93-1.87
		c6.38,0,10.42,3.17,10.42,9.98v14.88c0,0.24-0.14,0.38-0.38,0.38h-1.73c-0.24,0-0.43-0.14-0.43-0.38V97.5
		c0-5.38-2.83-7.73-7.87-7.73c-2.4,0-4.85,0.48-6.72,1.15v21.36c0,0.24-0.14,0.38-0.38,0.38H513z"/>
	<path class="st0" d="M555.28,78.73c0-0.24,0.14-0.38,0.38-0.38h1.73c0.29,0,0.43,0.14,0.43,0.38v32.31c0,0.19-0.1,0.38-0.34,0.43
		c-2.64,1.06-5.86,1.73-8.93,1.73c-6.29,0-10.42-3.17-10.42-10.32V97.7c0-6.77,4.03-10.27,10.23-10.27c2.59,0,4.99,0.77,6.91,1.92
		V78.73z M548.61,110.9c2.4,0,4.8-0.43,6.67-1.1v-18c-1.87-1.25-4.22-2.06-6.72-2.06c-4.99,0-7.82,2.4-7.82,7.97v5.18
		C540.74,108.59,543.62,110.9,548.61,110.9z"/>
	<path class="st0" d="M583.6,101.25c0,0.24-0.19,0.38-0.43,0.38h-16.56v2.69c0,4.18,3.26,6.58,7.25,6.58c3.6,0,6.05-1.54,7.82-3.07
		c0.24-0.14,0.43-0.14,0.58,0.1l0.86,1.1c0.19,0.19,0.19,0.38-0.05,0.58c-2.21,1.92-5.18,3.6-9.26,3.6c-5.09,0-9.79-3.17-9.79-8.88
		v-7.58c0-6.14,4.37-9.31,9.84-9.31c5.42,0,9.74,3.17,9.74,9.31V101.25z M573.86,89.78c-4.37,0-7.25,2.35-7.25,6.96v2.74h14.5v-2.74
		C581.11,92.18,578.08,89.78,573.86,89.78z"/>
	<path class="st0" d="M606.93,112.19c0.19,0.24,0.1,0.48-0.24,0.48h-2.16c-0.19,0-0.38-0.1-0.48-0.24l-7.54-10.51l-7.58,10.51
		c-0.1,0.14-0.29,0.24-0.48,0.24h-2.16c-0.34,0-0.43-0.24-0.24-0.48l8.88-12.1l-8.35-11.67c-0.14-0.24-0.05-0.48,0.24-0.48h2.11
		c0.19,0,0.38,0.1,0.48,0.29l7.1,10.03l7.06-10.03c0.1-0.19,0.34-0.29,0.48-0.29h2.11c0.29,0,0.43,0.24,0.24,0.48l-8.35,11.67
		L606.93,112.19z"/>
</g>
<line stroke-width="2" stroke-miterlimit="10" class="st1" x1="289.38" y1="23.35" x2="289.38" y2="114.08"/>
</svg>
"""

# For testing purposes
if __name__ == '__main__':
	pdf = generate_pdf(1024)
	with open('test.pdf', 'wb') as f:
		f.write(pdf)

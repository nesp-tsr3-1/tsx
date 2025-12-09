from fpdf import FPDF, TextStyle
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
from datetime import datetime
from textwrap import dedent
import urllib.request
import zipfile
from tsx.util import get_resource

# These lines are necessary to stop MatplotLib from trying to initialize
# GUI backend and crashing due to not being on the main thread:
import matplotlib
matplotlib.use('agg')

# Using a built-in PDF font for now
font_name='Inter'

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
		h_margin = 15
		self.set_y(-30)
		self.set_font(font_name, size=7, style="B")
		self.set_text_color(tsx_green)
		self.set_fill_color(white) # This is needed for text color to be correct, don't know why
		self.set_x(h_margin) # For some reason if I put this at the top of the method it doesn't work
		self.cell(text="www.tsx.org.au", new_y="NEXT", new_x="LEFT", h=5)
		self.set_font(font_name, size=7)
		self.set_char_spacing(spacing=-0.1)
		self.cell(text="E tsx@tern.org.au | @AusTSX | The University of Queensland, Long Pocket Precinct, Level 5 Foxtail Bld #1019 | 80 Meiers Rd, Indooroopilly QLD 4068 Australia", new_x="LEFT")
		self.set_fill_color("#F2F2F2")
		self.rect(x=0, y=self.h-20, w=self.w, h=20, style="F")
		self.set_fill_color("#000000")
		self.rect(x=0, y=self.h-2.5, w=self.w, h=2.5, style="F")
		self.set_y(-20)
		self.set_x(h_margin)
		self.image(footer_png, w=self.w - h_margin * 2)

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
		radius = 3.5/2
		pdf.circle(x=pdf.get_x()+1+radius, y=pdf.get_y()+0.5+radius, radius=radius, style=style)
		pdf.set_x(pdf.get_x() + 6)
		pdf.body(option['description'])
		pdf.ln()
	pdf.ln()

def text_in_box(pdf, text):
	with pdf.local_context():
		pdf.set_fill_color(light_grey)
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
		pdf.ln()

def numbered_question(pdf, number, text):
	pdf.set_margins(15, 10)
	pdf.set_font(font_name, size=10, style="B")
	number_text = "%s." % str(number)
	pdf.write(text=number_text, h=5)
	pdf.set_x(22)
	pdf.set_margins(22, 10)
	pdf.write(text=text, h=5)
	pdf.ln(h=6)

def unnumbered_question(pdf, text):
	pdf.set_font(font_name, size=10, style="B")
	pdf.write(text=text, h=5)
	pdf.ln(h=6)

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

def para(pdf, text):
	pdf.multi_cell(text=text, h=5, w=0, markdown=True)
	pdf.ln()

def bullet(pdf):
	pdf.circle(
		x=pdf.get_x() - 2,
		y=pdf.get_y() + 2.2,
		radius=0.7,
		style="F")

def setup_font(pdf):
	# Download font if necessary
	font_url = "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip"
	font_dir = data_dir("font")
	os.makedirs(font_dir, exist_ok=True)

	inter_font_dir = os.path.join(font_dir, "Inter-4.0")
	if not os.path.exists(inter_font_dir):
		local_filename, headers = urllib.request.urlretrieve(font_url)
		with zipfile.ZipFile(local_filename, 'r') as zip:
			zip.extractall(inter_font_dir)

	# Add font to PDF
	inter_font_path = os.path.join(data_dir("font"), "Inter-4.0", "extras", "ttf", "Inter%s.ttf")
	for style, suffix in [('', '-Regular'), ('B', '-Bold'), ('I', '-Italic')]:
		pdf.add_font('Inter', style, inter_font_path % suffix, uni=True)

def break_if_near_bottom(pdf):
	if pdf.will_page_break(60):
		pdf.add_page()

def generate_pdf(form_id):
	form = json.loads(get_form_json_raw(form_id))

	pdf = PDF(form['feedback_status']['code'].capitalize())

	# Set up font
	setup_font(pdf)

	pdf.set_title("TSX Custodian Feedback Form %s" % form_id)
	pdf.set_auto_page_break(True, 30)
	pdf.reset_margin()
	pdf.add_page()
	pdf.set_font(font_name, size=12)
	pdf.h1("Custodian Feedback Form")
	pdf.set_font(font_name, size=14)
	pdf.title_text(form['taxon']['scientific_name'] + " (" + form['dataset_id'] + ")")
	pdf.ln()


	# ---- Conditions and consent -----

	pdf.h2("Conditions and consent")

	pdf.set_font(font_name, size=10)
	para(pdf, dedent("""
		These feedback forms are based on the species monitoring data generously donated by you or your organisation as a data custodian for the development of Australia's Threatened Species Index. The index will allow for integrated reporting at national, state and regional levels, and track changes in threatened species populations. The goal of this feedback process is to inform decisions about which datasets will be included in the overall multi-species index. If custodians deem datasets to be unrepresentative of true species trends, these may be excluded from final analyses.

		Within your individual datasets (see the ‘Datasets’ tab) you can access a clean version of your processed data in a (1) raw (confidential) and (2) aggregated format (to be made open to the public unless embargoed). For your aggregated data, please note that site names will be masked and spatial information on site locations will be denatured to the IBRA subregion centroids before making the data available to the public. We use the 'Living Planet Index' method to calculate trends (Collen et al. 2009) and follow their requirements on data when we assess suitability of data for trends.

		The information we collect from you using these forms is part of an elicitation process for the project “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species”. We would like to inform you of the following:
		""".strip()))

	# Bulleted list requires special handling
	pdf.set_x(22)
	pdf.set_margins(22, 10)
	bullet(pdf)
	para(pdf, "Data collected will be anonymous and you will not be identified by name in any publication arising from this work without your consent.")
	bullet(pdf)
	para(pdf, "All participation in this process is voluntary. If at any time you do not feel comfortable providing information, you have the right to withdraw any or all of your input to the project.")
	bullet(pdf)
	para(pdf, "Data collected from this study will be used to inform the Threatened Species Index at national and various regional scales.")
	bullet(pdf)
	para(pdf, "Project outputs will include a web tool and a publicly available aggregated dataset that enables the public to interrogate trends in Australia’s threatened species over space and time.")
	pdf.reset_margin()

	para(pdf, """
		This study adheres to the Guidelines of the ethical review process of The University of Queensland and the National Statement on Ethical Conduct in Human Research. Whilst you are free to discuss your participation in this study with project staff (Project Manager Tayla Lawrie: [t.lawrie@uq.edu.au](mailto:t.lawrie@uq.edu.au) or **0476 378 354**), if you would like to speak to an officer of the University not involved in the study, you may contact the Ethics Coordinator on 07 3443 1656.

		Your involvement in this elicitation process constitutes your consent for the Threatened Species Index team to use the information collected in research, subject to the information provided above. For more information about this expert elicitation process, please [click here](https://tsx.org.au/data/TSX_Custodian_Feedback_Participant_Information_Sheet_Sep24.pdf) to download our participant information sheet.

		**References**

		Collen, B., J. Loh, S. Whitmee, L. McRae, R. Amin, and J. E. Baillie. 2009. Monitoring change in vertebrate abundance: the living planet index. Conserv Biol 23:317-327.
		""".strip())

	unnumbered_question(pdf, "I have read and understood the conditions of the expert elicitation study for the project, “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species” and provide my consent.")
	multiple_choice_options(pdf,
		[{ "id": "agree", "description": "I Agree" }],
		"agree" if form['answers'].get('consent_given') else "")

	unnumbered_question(pdf, "Please enter your name")
	text_in_box(pdf, get_answer(form, 'consent_name'))

	pdf.add_page()


	# ----- Data citation and monitoring aims ------

	pdf.h2("Data citation and monitoring aims")
	pdf.h3("Data Citation")
	pdf.body(citation(form))
	pdf.ln()
	pdf.ln()

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 1, "Do you agree with the above suggested citation for your data? If no, please indicate how to correctly cite your data.")
		multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('citation_agree'))
		text_in_box(pdf, get_answer(form, 'citation_agree_comments'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 2, "Has your monitoring program been explicitly designed to detect population trends over time? If no / unsure, please indicate the aims of your monitoring.")
		multiple_choice_options(pdf, field_options['yes_no_unsure'], form['answers'].get('monitoring_for_trend'))
		text_in_box(pdf, get_answer(form, 'monitoring_for_trend_comments'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 3, "Do you analyse your own data for trends? If no, please indicate why.")
		multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('analyse_own_trends'))
		text_in_box(pdf, get_answer(form, 'analyse_own_trends_comments'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 4, "Can you estimate what percentage (%) of your species' population existed in Australia at the start of your monitoring (assuming this was 100% in 1750)? This information is to help understand population baselines and determine whether the majority of a species' decline may have occurred prior to monitoring.")
		text_in_box(pdf, get_answer(form, 'pop_1750'))
		if get_answer(form, 'pop_1750').lower() == 'unsure':
			text_in_box(pdf, get_answer(form, 'pop_1750_comments'))

	pdf.add_page()


	# ----- Data summary and processing -----

	pdf.reset_margin()
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
	headings_style = FontFace(emphasis="BOLD", fill_color=light_grey)
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

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 5, "Does the above data summary and plots appear representative of your dataset?")
		multiple_choice_options(pdf, field_options['yes_no'], form['answers'].get('data_summary_agree'))
		text_in_box(pdf, get_answer(form, 'data_summary_agree_comments'))


	# Proof of concept of code to avoid page-breaks within a section
	# (pdf.unbreakable() doesn't work with get_y())
	for doc in avoid_break(pdf):
		numbered_question(doc, 6, "Do you agree with how your data were handled? If no, please suggest an alternative method of aggregation.")
		multiple_choice_options(doc, field_options['yes_no_unsure'], form['answers'].get('processing_agree'))

		text_in_box(doc, get_answer(form, 'processing_agree_comments'))


	# ------- Statistics and trend estimate --------

	pdf.reset_margin()
	break_if_near_bottom(pdf)
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

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 7, "Do the above statistics appear representative of your dataset?")
		multiple_choice_options(pdf, field_options['yes_no_unsure'], form['answers'].get('statistics_agree'))
		text_in_box(pdf, get_answer(form, 'statistics_agree_comments'))

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

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 8, "Do you agree with the trend estimate? If no or unsure, please elaborate (include detail on trends for specific sites where relevant).")
		multiple_choice_options(pdf, field_options['yes_no_unsure'], form['answers'].get('trend_agree'))
		text_in_box(pdf, get_answer(form, 'trend_agree_comments'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 9, "Looking at the trend for your data, what should be the reference year at which the index should start?")
		text_in_box(pdf, get_answer(form, 'start_year'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 10, "Looking at the trend for your data, what should be the year at which the index should end?")
		text_in_box(pdf, get_answer(form, 'end_year'))

	pdf.add_page()

	# ------------ Data Suitability ------------
	pdf.reset_margin()
	pdf.h2("Data Suitablility")

	pdf.body("The below fields relate to the suitability of your data for demonstrating trends in populations over time. After reading the descriptions, please select the most suitable option.")
	pdf.ln()
	pdf.ln()

	pdf.set_fill_color(white)
	pdf.set_font(font_name, size=8)

	with pdf.table(
		line_height=4,
		padding=2,
		text_align="LEFT",
		headings_style=headings_style,
		col_widths=(3, 3, 0.5, 1, 4)
		) as table:
		headings = table.row()
		headings.cell('Suitablility criteria')
		headings.cell('Description')
		headings.cell('Your assessment', colspan=3)

		form_fields_by_name = { f.name: f for f in form_fields }

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
					row.cell(img=filled_circle)
				else:
					row.cell(img=empty_circle)

				row.cell(str(option['id']))
				row.cell(str(option['description']).encode('ascii', 'ignore').decode('ascii'))

	pdf.ln()

	unnumbered_question(pdf, "Please add any additional comments on data suitability and the criteria below.")
	text_in_box(pdf, get_answer(form, 'data_suitability_comments'))
	pdf.ln()


	# ------------ Additional Comments ------------

	for pdf in avoid_break(pdf):
		pdf.h2("Additional Comments")
		unnumbered_question(pdf, "Please provide any additional comments about this dataset and/or trend below.")
		text_in_box(pdf, get_answer(form, 'additional_comments'))

	# ------------ Monitoring program funding etc. ---

	pdf.reset_margin()

	for pdf in avoid_break(pdf):
		pdf.h2("Monitoring program funding, logistics and governance")
		numbered_question(pdf, 16, "Please indicate if you would prefer to provide this information via a phone or video call with our project team:")
		multiple_choice_options(pdf, field_options['monitoring_program_information_provided'], form['answers'].get('monitoring_program_information_provided'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 17, "Effort: How much time on average per year was spent on project labour, i.e. data collection in the field?")
		answer_table(pdf, form, [
			('a. Days/year paid labour:', 'effort_labour_paid_days_per_year'),
			('b. Days/year volunteered time:', 'effort_labour_volunteer_days_per_year')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 18, "Effort: How much time on average per year was spent on project overheads, e.g. data collation and dataset maintenance?")
		answer_table(pdf, form, [
			('a. Days/year paid labour:', 'effort_overheads_paid_days_per_year'),
			('b. Days/year volunteered time:', 'effort_overheads_volunteer_days_per_year')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 19, "Effort: Approximately how many people were involved in the last bout of monitoring (including both field and office work)")
		answer_table(pdf, form, [
			('a. Paid staff:', 'effort_paid_staff_count'),
			('b. Volunteers:', 'effort_volunteer_count')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 20, "Funding: How much do you think in AUD$ a single survey costs (not counting in-kind support)?")
		text_in_box(pdf, get_answer(form, 'funding_cost_per_survey_aud'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 21, "Funding: Can you estimate in AUD$ the total investment in the dataset to date (again not counting in-kind support)?")
		text_in_box(pdf, get_answer(form, 'funding_total_investment_aud'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 22, "Funding: Who has been paying for the monitoring? (e.g. government grants, research funds, private donations etc. - list multiple funding sources if they have been needed over the years)")
		answer_table(pdf, form, [
			('a. Government grants:', 'funding_source_government_grants', 'yes_no'),
			('b. Research funds:', 'funding_source_research_funds', 'yes_no'),
			('c. Private donations:', 'funding_source_private_donations',  'yes_no'),
			('d. Other:', 'funding_source_other'),
			('e. Can you estimate the total number of funding sources so far?:', 'funding_source_count')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 23, "Leadership: Who has been providing the drive to keep the monitoring going after the baseline was established?")
		text_in_box(pdf, get_answer(form, 'leadership'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 24, "Impact: Are data being used to directly inform management of the threatened species or measure the effectiveness of management actions?")
		answer_table(pdf, form, [
			('a.', 'impact_used_for_management', 'yes_no'),
			('b. Please expand:', 'impact_used_for_management_comments')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 25, "Impact: Is your organisation responsible for managing this species in the monitored area?")
		text_in_box(pdf, get_answer(form, 'impact_organisation_responsible'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 26, "Impact: Can you describe any management that has changed because of the monitoring?")
		text_in_box(pdf, get_answer(form, 'impact_management_changes'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 27, "Data availability: Is your monitoring data readily available to the public (e.g. through reports, or on website). If not, can the public access it?")
		text_in_box(pdf, get_answer(form, 'data_availability'))

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 28, "Succession: Do you have commitments to extend the monitoring into the future?")
		answer_table(pdf, form, [
			('a.', 'succession_commitment', 'yes_no'),
			('b. Please expand:', 'succession_commitment_comments')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 29, "Succession: Have you developed a plan for continual monitoring when the current organisers/you need to stop?")
		answer_table(pdf, form, [
			('a.', 'succession_plan', 'yes_no'),
			('b. Please expand:', 'succession_plan_comments')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 30, "Design: Was there thought about the statistical power of the monitoring when it was started (i.e. the probability that change could be detected?)")
		answer_table(pdf, form, [
			('a.', 'design_statistical_power', 'yes_no'),
			('b. Please expand:', 'design_statistical_power_comments')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 31, "Design: Is anything other than the numbers of threatened species being monitored at the same time that could explain changes in abundance (e.g. prevalence of a threat, fire, breeding success, etc?)")
		answer_table(pdf, form, [
			('a.', 'design_other_factors', 'yes_no'),
			('b. Please expand:', 'design_other_factors_comments')])

	for pdf in avoid_break(pdf):
		numbered_question(pdf, 32, "Co-benefits: Is the monitoring program for this species also collecting trend information on other threatened species?")
		answer_table(pdf, form, [
			('a.', 'co_benefits_other_species', 'yes_no'),
			('b. Please expand:', 'co_benefits_other_species_comments')])


	return bytes(pdf.output())

def checkbox_symbol_str(filled):
	return "[x]" if filled else "[ ]"

def options_to_str(options, selected_option=None):
	parts = [checkbox_symbol_str(selected_option == option['id']) + " " + option['description'] for option in options]
	return " ".join(parts)

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
		for row_data in rows:
			title, field = row_data[:2]
			row = table.row()
			row.cell(title)
			if len(row_data) == 3:
				options = field_options[row_data[2]]
				row.cell(options_to_str(options, get_answer(form, field)))
			else:
				row.cell(get_answer(form, field))

	pdf.ln()
	pdf.ln()

def get_answer(form, field):
	return str(form['answers'].get(field, '') or '')

def format_int(x):
	return f'{x:,}'

def format_decimal(x):
	return f'{x:,.2f}'

def consistency_plot_svg(data):
	xys = [(year, i + 1) for i, series in enumerate(data) for year, count in series]
	x, y = zip(*xys)

	fig = plt.figure(figsize=(6, 4.5))
	ax = fig.gca()
	ax.yaxis.get_major_locator().set_params(integer=True)
	ax.xaxis.get_major_locator().set_params(integer=True)
	plt.xlabel('Year')
	plt.ylabel('Sites (time series)')
	plt.grid(True, color='#ddd')
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

	# Note: we can currently assume for custodian feedback surveys that
	# number of species is always one. However, if this changes, the following
	# code will render single species trends using a dashed line as required.

	# num_species = [int(x) for x in num_species]
	# single_species = [x == 1 for x in num_species]
	# single_species_dilated = [a or b or c for a, b, c in zip(
	# 	single_species[1:] + [False],
	# 	single_species,
	# 	[False] + single_species[:-1])
	# ]
	# trend_solid = [None if single_species[i] else trend[i] for i in range(len(trend))]
	# trend_dashed = [trend[i] if single_species_dilated[i] else None for i in range(len(trend))]

	fig = plt.figure(figsize=(12, 4.5))
	plt.xlabel('Year')
	plt.ylabel('Index (%s = 1)' % years[0])
	plt.grid(True, color='#ddd')
	plt.plot(years, trend, linestyle='dashed')
	# plt.plot(years, trend_solid, color='tab:blue')
	# plt.plot(years, trend_dashed, color='tab:blue', linestyle='dashed')
	plt.gca().set_xlim(years[0], years[-1])
	ax = fig.gca()
	ax.xaxis.get_major_locator().set_params(integer=True)
	# Note: hatch fill doesn't work because it produces an SVG that PyPDF can't render
	plt.fill_between(years, lower, upper, color=light_grey)

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
	gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, color='#00000020')
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
light_grey = "#F4F4F4"
tsx_green = "#266F6A"

footer_png = get_resource("pdf-footer.png").read_bytes()
tsx_logo_svg = get_resource("pdf-logo.svg").read_bytes()

filled_circle = BytesIO(b"<svg version='1.1' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'><circle cx='10' cy='10' r='10' stroke-width='1' stroke='black' fill='#266F6A' /></svg>")
empty_circle = BytesIO(b"<svg version='1.1' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'><circle cx='10' cy='10' r='10' stroke-width='1' stroke='black' /></svg>")

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

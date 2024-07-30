<template>
  <div class="section">
    <div class="container feedback-home">
      <div class="columns">
<!-- <aside class="menu" v-if="status == 'loaded'">
    <ul class="menu-list">
      <li><a>Data citation and monitoring aims</a></li>
      <li><a>Data summary and processing</a></li>
      <li><a>Statistics and trend estimate</a></li>
      <li><a>Data suitability</a></li>
      <li><a>Funding, logistics and governance (optional)</a></li>
    </ul>
  </aside> -->
        <div class="column is-10 is-offset-1">
          <user-nav></user-nav>
          <div v-if="status == 'loading'">
            <p>
              Loading…
            </p>
          </div>
          <div v-if="status == 'error'">
            <p>
              Failed to load form.
            </p>
          </div>

          <div v-if="status === 'loaded'">

            <!-- <div style="white-space: pre;">{{formJSON}}</div> -->

            <div class="columns">
              <div class="column">
                <h2 class="title">{{form.taxon.scientific_name}}</h2>
                <p class="content">
                  <span class="tag is-large">{{form.dataset_id}}</span>
                </p>
              </div>
              <div class="column is-narrow">
                <div class="buttons">
                  <button class="button is-primary" :disabled="!canSaveDraft" @click="saveAndClose">{{saveButtonLabel}}</button>
                  <button class="button is-primary" :disabled="!canSubmit">Submit</button>
                </div>
                <p class="help is-danger" v-if="saveStatus == 'error'">Failed to save form</p>
              </div>
            </div>

            <hr>

            <!---- Conditions and consent ---->

            <div v-if="notAdmin">
              <div class="content">
                <h3>Conditions and consent</h3>
                <p>
                  These feedback forms are based on the species monitoring data generously donated by you or your organisation as a data custodian for the development of Australia's Threatened Species Index. The index will allow for integrated reporting at national, state and regional levels, and track changes in threatened species populations. The goal of this feedback process is to inform decisions about which datasets will be included in the overall multi-species index. If custodians deem datasets to be unrepresentative of true species trends, these may be excluded from final analyses.
                </p>
                <p>
                  Within your individual datasets (see the ‘Datasets’ tab) you can access a clean version of your processed data in a (1) raw (confidential) and (2) aggregated format (to be made open to the public unless embargoed). For your aggregated data, please note that site names will be masked and spatial information on site locations will be denatured to the IBRA subregion centroids before making the data available to the public. We use the 'Living Planet Index' method to calculate trends (Collen et. 2009) and follow their requirements on data when we assess suitability of data for trends.
                </p>
                <p>
                  The information we collect from you using these forms is part of an elicitation process for the project “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species”. We would like to inform you of the following:
                </p>
                <ul>
                  <li>
                    Data collected will be anonymous and you will not be identified by name in any publication arising from this work without your consent.
                  </li>
                  <li>
                    All participation in this process is voluntary. If at any time you do not feel comfortable providing information, you have the right to withdraw any or all of your input to the project.
                  </li>
                  <li>
                    Data collected from this study will be used to inform the Threatened Species Index at national and various regional scales.
                  </li>
                  <li>
                    Project outputs will include a web tool and a publicly available aggregated dataset that enables the public to interrogate trends in Australia’s threatened species over space and time.
                  </li>
                </ul>
                <p>
                  This study adheres to the Guidelines of the ethical review process of The University of Queensland and the National Statement on Ethical Conduct in Human Research. Whilst you are free to discuss your participation in this study with project staff (Project Coordinator Tayla Lawrie: <a href='mailto:t.lawrie@uq.edu.au'>t.lawrie@uq.edu.au</a> or <b>0476 378 354</b>), if you would like to speak to an officer of the University not involved in the study, you may contact the Ethics Coordinator on 07 3443 1656.
                </p>
                <p>
                  Your involvement in this elicitation process constitutes your consent for the Threatened Species Index team to use the information collected in research, subject to the information provided above.
                </p>
                <p>
                  <b>References</b><br>
                  Collen, B., J. Loh, S. Whitmee, L. McRae, R. Amin, and J. E. Baillie. 2009. Monitoring change in vertebrate abundance: the living planet index. Conserv Biol 23:317-327.
                </p>
                <p>
                  <b>I have read and understand the conditions of the expert elicitation study for the project, “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species” and provide my consent.</b>
                </p>
              </div>
              <div class="indent">
                <div class="field">
                  <label class="checkbox required">
                    <input type="checkbox" v-model="formData.consent_given" />
                    I agree
                  </label>
                </div>
                <div class="field">
                  <label class="label required">Please enter your name.</label>
                  <div class="control">
                    <input class="input" type="text" placeholder="" v-model="formData.consent_name">
                  </div>
                </div>
              </div>
              <hr>
            </div>

            <!---- Data citation and monitoring aims ---->

            <div class="content">
              <h3>Data citation and monitoring aims</h3>
              <p>
                <b>Data citation</b><br>
                {{citation}}
              </p>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you agree with the above suggested citation for your data? If no, please indicate how to correctly cite your data.</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with the suggested citation? If no, what changes have they suggested to correctly cite their data?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="citation_ok" v-model="formData.citation_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="citation_ok" v-model="formData.citation_ok" value="no" /> No
                  </label>
                </div>
                <input class="input" type="text" placeholder="Suggested citation" v-if="formData.citation_ok == 'no'" v-model="formData.citation_suggestion">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Has your monitoring program been explicitly designed to detect population trends over time? If no / unsure, please indicate the aims of your monitoring.</label>
              <label class="label required" v-if="isAdmin">Is the monitoring program explicitly designed to detect population trends over time? If no or unsure, what are the aims of their monitoring?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="no" /> No
                  </label>
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="unsure" /> Unsure
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.designed_for_trends_comments" v-if="formData.designed_for_trends === 'no' || formData.designed_for_trends === 'unsure'">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you analyse your own data for trends?</label>
              <label class="label required" v-if="isAdmin">Does the custodian analyse their own data for trends?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="analysed_for_trends" v-model="formData.analysed_for_trends" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="analysed_for_trends" v-model="formData.analysed_for_trends" value="no" /> No
                  </label>
                </div>
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Can you estimate what percentage (%) of your species’ population existed in Australia at the start of your monitoring (assuming this was 100% in 1750)? <strong>This information is to help understand population baselines and determine whether the majority of a species' decline may have occurred prior to monitoring.</strong></label>
              <label class="label required" v-if="isAdmin">What has the custodian estimated to be the percentage (%) of the species’ population that existed in Australia at the start of the monitoring (assuming this was 100% in 1750)?</label>
              <div class="control indent">
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.estimated_population_baseline_percentage">
              </div>
            </div>

            <!---- Data summary and processing ---->

            <div class="content">
              <h3>Data summary and processing</h3>
            </div>

            <div class="columns">
              <div class="column is-half">
                <div v-if="consistencyPlotAvailable" class="content">
                      <canvas ref="consistencyPlot" style="height: 25em; max-height: 25em;"></canvas>
                      <hr>
                      <p style="font-style: italic;">
                        The above dot plot shows the distribution of surveys at unique sites. Each row represents a time series in the dataset or data subset where a species/subspecies was monitored with a consistent method and unit of measurement at a single site over time. The maximum number of time-series included in this plot is 50.
                      </p>
                </div>
                <div v-else class="content">
                  Consistency plot unavailable
                </div>
              </div>
              <div class="column is-half">
                <div v-if="intensityMapData" class="content">
                  <div style="width: 100%; max-width: 640px; height: 25em; display: block; background: #eee;">
                    <HeatMap :heatmap-data="intensityMapData"></HeatMap>
                  </div>
                  <hr>
                  <p style="font-style: italic;">
                    The above map shows the location of your monitoring sites.
                  </p>
                </div>
                <div v-else class="content">
                  Map unavailable
                </div>
              </div>
            </div>

            <div class="content">
              <table v-if="form?.stats?.processing_summary" class='table is-fullwidth is-striped is-bordered'>
                <thead>
                  <tr>
                    <th>Search Type Description (monitoring method)</th>
                    <th>Unit of Measurement</th>
                    <th>Unit Type</th>
                    <th>Data Processing Type</th>
                    <th>Method of Aggregation</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in form.stats.processing_summary">
                    <td>{{row.search_type}}</td>
                    <td>{{row.unit}}</td>
                    <td>{{row.unit_type}}</td>
                    <td></td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="content">
              <table v-if="form?.stats?.site_management_summary" class='table is-fullwidth is-striped is-bordered'>
                <thead>
                  <tr>
                    <th>Management Category</th>
                    <th>Management Comments</th>
                    <th>Number of Sites</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in form.stats.site_management_summary">
                    <td>{{row.management_category}}</td>
                    <td>{{row.management_comments}}</td>
                    <td>{{row.site_count.toLocaleString()}}</td>
                  </tr>
                </tbody>
              </table>
            </div>


            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Are the above values representative of your datasets?</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with the data summary? If no, what specifically do they disagree with?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="summary_ok" v-model="formData.summary_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="summary_ok" v-model="formData.summary_ok" value="no" /> No
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-if="formData.summary_ok == 'no'" v-model="formData.summary_comments">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you agree with how your data were handled? If no, please suggest an alternative method of aggregation.</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with how the data were processed? If no, what alternative method of aggregation have they suggested?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="processing_ok" v-model="formData.processing_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="processing_ok" v-model="formData.processing_ok" value="no" /> No
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-if="formData.processing_ok == 'no'" v-model="formData.processing_comments">
              </div>
            </div>

             <!---- Statistics and Trend Estimate ---->

            <div class="content">
              <h3>Statistics and trend estimate</h3>
            </div>

            <div class="content">
              <table class='table is-fullwidth is-striped is-bordered'>
                <thead>
                  <tr>
                    <th>Statistics (units)</th>
                    <th>Mean (±SD)</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="stats in [form?.stats?.raw_data_stats].filter(x=>x)">
                    <tr>
                      <td colspan="2"><b>Raw data</b></td>
                    </tr>
                    <tr>
                      <td>Period of monitoring (years)</td>
                      <td>{{stats.min_year}}–{{stats.max_year}}</td>
                    </tr>
                    <tr>
                      <td>Number of data points (surveys)</td>
                      <td>{{stats.survey_count.toLocaleString()}}</td>
                    </tr>
                    <tr>
                      <td>Range of raw data (counts)</td>
                      <td>{{stats.min_count.toLocaleString()}}–{{stats.max_count.toLocaleString()}}</td>
                    </tr>
                    <tr>
                      <td>Number of 0 counts</td>
                      <td>{{stats.zero_counts.toLocaleString()}}</td>
                    </tr>
                  </template>
                  <template v-for="stats in [form?.stats?.time_series_stats].filter(x=>x)">
                    <tr>
                      <td colspan="2"><b>Aggregated data</b></td>
                    </tr>
                    <tr>
                      <td>Number of repeatedly monitored sites (time series)</td>
                      <td>{{stats.time_series_count.toLocaleString()}}</td>
                    </tr>
                    <tr>
                      <td>Time-series length (years)</td>
                      <td>{{formatDecimal(stats.time_series_length_mean)}}
                        (±{{formatDecimal(stats.time_series_length_std)}})</td>
                    </tr>
                    <tr>
                      <td>Time-series sample years (years)</td>
                      <td>{{formatDecimal(stats.time_series_sample_years_mean)}}
                        (±{{formatDecimal(stats.time_series_sample_years_std)}})</td>
                    </tr>
                    <tr>
                      <td>Time-series completeness (%)</td>
                      <td>{{formatDecimal(stats.time_series_completeness_mean)}}
                        (±{{formatDecimal(stats.time_series_completeness_std)}})</td>
                    </tr>
                    <tr>
                      <td>Time series sampling evenness (0 = very even sampling)</td>
                      <td>{{formatDecimal(stats.time_series_sampling_evenness_mean)}}
                        (±{{formatDecimal(stats.time_series_sampling_evenness_std)}})</td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do the above statistics appear representative of your dataset?</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with the data statistics (raw and aggregated)? If no, what specifically do they disagree with?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="statistics_ok" v-model="formData.statistics_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="statistics_ok" v-model="formData.statistics_ok" value="no" /> No
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-if="formData.statistics_ok == 'no'" v-model="formData.statistics_comments">
              </div>
            </div>

            <div class="content">
              <div v-if="trendPlotAvailable" class="content">
                <canvas ref="trendPlot" style="height: 10em;"></canvas>
                  <hr>
                  <p style="font-style: italic;">
                    The above graph shows the estimated yearly change in relative abundance in relation to a baseline year where the index is set to 1. Changes are proportional - a value of 0.5 indicates the population is 50% below the baseline value; a value of 1.5 indicates 50% above baseline. The overall trend (mean value per year) is shown by the blue line - this line is used in the final multi-species TSX. The grey cloud indicates the uncertainty in the estimate as measured by the variability between all-time series in your dataset.
                  </p>
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you agree with the trend estimate? If no or unsure, please elaborate (include detail on trends for specific sites where relevant).</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with the trend? If no or unsure, what specifically do they disagree with?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="trend_ok" v-model="formData.trend_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="trend_ok" v-model="formData.trend_ok" value="no" /> No
                  </label>
                  <label class="radio">
                    <input type="radio" name="trend_ok" v-model="formData.trend_ok" value="unsure" /> Unsure
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-if="formData.trend_ok == 'no' || formData.trend_ok == 'unsure'" v-model="formData.trend_comments">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Looking at the trend for your data, what should be the reference year at which the index should start?</label>
              <label class="label required" v-if="isAdmin">What reference year has the custodian suggested for their trend?</label>
              <div class="control indent">
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.trend_ref_year">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Looking at the trend for your data, what should be the year at which the index should end?</label>
              <label class="label required" v-if="isAdmin">What end year has the custodian suggested for their trend?</label>
              <div class="control indent">
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.trend_end_year">
              </div>
            </div>

            <!---- Data suitability ---->

            <div class="content">
              <h3>Data suitability</h3>
            </div>

            <div class="content">
              <p>
                The below fields relate to the suitability of your data for demonstrating trends in population over time. After reading the descriptions, please select the most suitable option.
              </p>
              <table class='table is-fullwidth is-striped is-bordered'>
                <thead>
                  <tr>
                    <th>Suitability criteria</th>
                    <th>Description</th>
                    <th colspan="3">Your assessment</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td :rowspan="options.standardisationOfMethodEffort.length + 1">
                      <div class="field numbered">
                        <label class="label required">Standardisation of method effort</label>
                      </div>
                    </td>
                    <td :rowspan="options.standardisationOfMethodEffort.length + 1">
                      This data suitability indicator rates the degree of standardisation of monitoring method/effort and is assessed to the data source level by enquiring with the data custodian and examining data.
                    </td>
                  </tr>
                  <tr v-for="option in options.standardisationOfMethodEffort"
                    @click="() => { formData.standardisation_of_method_effort = option.id}">
                    <td><input type='radio' name='standardisation_of_method_effort' :value="option.id" v-model="formData.standardisation_of_method_effort"></td>
                    <td>{{option.id}}</td>
                    <td>{{option.description}}</td>
                  </tr>

                  <tr>
                    <td :rowspan="options.objectiveOfMonitoring.length + 1">
                      <div class="field numbered">
                        <label class="label required">Objective of monitoring</label>
                      </div>
                    </td>
                    <td :rowspan="options.objectiveOfMonitoring.length + 1">
                      This field indicates the objective of the monitoring.
                    </td>
                  </tr>
                  <tr v-for="option in options.objectiveOfMonitoring"
                    @click="() => { formData.objective_of_monitoring = option.id}">
                    <td><input type='radio' name='objective_of_monitoring' :value="option.id" v-model="formData.objective_of_monitoring"></td>
                    <td>{{option.id}}</td>
                    <td>{{option.description}}</td>
                  </tr>

                  <tr>
                    <td :rowspan="options.consistencyOfMonitoring.length + 1">
                      <div class="field numbered">
                        <label class="label required">Consistency of monitoring</label>
                      </div>
                    </td>
                    <td :rowspan="options.consistencyOfMonitoring.length + 1">
                      This data suitability indicator rates the degree of consistency by which the same sites were repeatedly monitored over time.
                    </td>
                  </tr>
                  <tr v-for="option in options.consistencyOfMonitoring"
                    @click="() => { formData.consistency_of_monitoring = option.id}">
                    <td><input type='radio' name='consistency_of_monitoring' :value="option.id" v-model="formData.consistency_of_monitoring"></td>
                    <td>{{option.id}}</td>
                    <td>{{option.description}}</td>
                  </tr>

                  <tr>
                    <td :rowspan="options.monitoringFrequencyAndTiming.length + 1">
                      <div class="field numbered">
                        <label class="label required">Monitoring frequency and timing</label>
                      </div>
                    </td>
                    <td :rowspan="options.monitoringFrequencyAndTiming.length + 1">
                      This data suitability indicator rates whether the taxon was monitored with an appropriate frequency and during an appropriate season/timing.
                    </td>
                  </tr>
                  <tr v-for="option in options.monitoringFrequencyAndTiming"
                    @click="() => { formData.monitoring_frequency_and_timing = option.id}">
                    <td><input type='radio' name='monitoring_frequency_and_timing' :value="option.id" v-model="formData.monitoring_frequency_and_timing"></td>
                    <td>{{option.id}}</td>
                    <td>{{option.description}}</td>
                  </tr>

                  <tr>
                    <td :rowspan="options.absencesRecorded.length + 1">
                      <div class="field numbered">
                        <label class="label required">Were absences recorded systematically?</label>
                      </div>
                    </td>
                    <td :rowspan="options.absencesRecorded.length + 1">
                      Absences are non-detections of taxa i.e. where 0 counts of a species are recorded.
                    </td>
                  </tr>
                  <tr v-for="option in options.absencesRecorded"
                    @click="() => { formData.absences_recorded = option.id}">
                    <td><input type='radio' name='absences_recorded' :value="option.id" v-model="formData.absences_recorded"></td>
                    <td colspan="2">{{option.description}}</td>
                  </tr>
                </tbody>
              </table>

              <div class="field">
                <label class="label" v-if="notAdmin">Please add any additional comments on data suitability and the criteria below.</label>
                <label class="label" v-if="isAdmin">What additional comments on data suitability and the criteria has the custodian provided?</label>
                <div class="control">
                  <input class="input" type="text" placeholder="Enter your answer" v-model="formData.data_suitability_comments">
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { handleLinkClick, formatDateTime } from '../util.js'
import { generateCitation } from '../util.js'
import { plotConsistency } from '../plotConsistency.js'
import { plotTrend, generateTrendPlotData } from '../plotTrend.js'
import HeatMap from './HeatMap.vue'

let options = {
  standardisationOfMethodEffort: [
    {
      id: 6,
      description: "Pre-defined sites/plots surveyed repeatedly through time using a single standardised method and effort across the whole monitoring program"
    },
    {
      id: 5,
      description: "Pre-defined sites/plots surveyed repeatedly through time with methods and effort standardised within site units, but not across program - i.e. different sites surveyed have different survey effort/methods"
    },
    {
      id: 4,
      description: "Pre-defined sites/plots surveyed repeatedly through time with varying methods and effort"
    },
    {
      id: 3,
      description: "Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping possible - e.g. a lot of fixed area/time searches conducted within a region but not at pre-defined sites"
    },
    {
      id: 2,
      description: "Data collection using standardised methods and effort but surveys not site-based (i.e. surveys spatially ad-hoc). Post-hoc site grouping not possible"
    },
    {
      id: 1,
      description: "Unstandardised methods/effort, surveys not site-based"
    }
  ],
  objectiveOfMonitoring: [
    {
      id: 4,
      description: "Monitoring for targeted conservation management"
    },
    {
      id: 3,
      description: "Monitoring for general conservation management – ‘surveillance’ monitoring"
    },
    {
      id: 2,
      description: "Baseline monitoring"
    },
    {
      id: 1,
      description: "Monitoring for community engagement"
    },
    {
      id: 'NA',
      description: "Not defined"
    }
  ],
  consistencyOfMonitoring: [
    {
      id: 4,
      description: "Balanced; all (or virtually all) sites surveyed in each year sampled (no, or virtually no, site turnover)"
    },
    {
      id: 3,
      description: "Imbalanced (low turnover); sites surveyed consistently through time as established, but new sites are added to program with time."
    },
    {
      id: 2,
      description: "Imbalanced (high turnover); new sites are surveyed with time, but monitoring of older sites is often not always maintained."
    },
    {
      id: 1,
      description: "Highly Imbalanced (very high turnover); different sites surveyed in different sampling periods. Sites are generally not surveyed consistently through time (highly biased)"
    }
  ],
  monitoringFrequencyAndTiming: [
    {
      id: 3,
      description: "Monitoring frequency and timing appropriate for taxon"
    },
    {
      id: 2,
      description: "Monitoring frequency or timing inappropriate for taxon for majority of data."
    },
    {
      id: 1,
      description: "Monitoring ad-hoc; no pattern to surveys for majority of data (incidental)"
    }
  ],
  absencesRecorded: [
    {
      id: "yes",
      description: "Yes"
    },
    {
      id: "no",
      description: "No"
    },
    {
      id: "partially",
      description: "Partially (for some of the survey period)"
    }
  ]
}

export default {
  name: 'CustodianFeedbackForm',
  components: {
    HeatMap
  },
  data () {
    return {
      currentUser: null,
      status: 'loading',
      saveStatus: 'none',
      formId: this.$route.params.id,
      form: null,
      formData: {

      },
      options
    }
  },
  created() {
    this.refresh()
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })

    api.currentUser().then(currentUser => {
      this.currentUser = currentUser
    }).catch(error => {
      this.error = error
    })
  },
  computed: {
    showConsent() {
      return true
    },
    citation() {
      let source = this.form.source
      return source && generateCitation(source.authors, source.details, source.provider)
    },
    isAdmin() {
      return this.form.feedback_type.code === 'admin'
    },
    notAdmin() {
      return this.form.feedback_type.code !== 'admin'
    },
    formJSON() {
      return JSON.stringify(this.formData, null, 4);
    },
    saveButtonLabel() {
      if(this.saveStatus == 'saving') {
        return 'Saving…'
      } else {
        return 'Save Draft'
      }
    },
    canSaveDraft() {
      return this.saveStatus != 'saving'
    },
    canSubmit() {
      // TODO
      return false
    },
    consistencyPlotAvailable() {
      return !!this.form?.stats?.monitoring_consistency
    },
    intensityMapData() {
      return this.form?.stats?.intensity_map
    },
    trendPlotAvailable() {
      return !!this.form?.stats?.trend
    }
  },
  watch: {
    consistencyPlotAvailable(isAvailable) {
      let data = this.form?.stats?.monitoring_consistency
      if(isAvailable && data) {
        setTimeout(() => {
          plotConsistency(data, this.$refs.consistencyPlot)
        })
      }
    },
    trendPlotAvailable(isAvailable) {
      let data = this.form?.stats?.trend
      if(isAvailable && data) {
        setTimeout(() => {
          plotTrend(data, this.$refs.trendPlot)
        })
      }
    }
  },
  methods: {
    refresh() {
      api.custodianFeedbackForm(this.formId).then((form) => {
        this.form = form
        this.formData = { ... form.answers } // TODO: use a better name than 'formData'
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    formatDateTime,
    formatDecimal(x) {
      return x.toLocaleString(undefined, { maximumFractionDigits: 2 })
    },
    save(close) {
      let json = { ... this.formData }
      this.saveStatus = 'saving'
      setTimeout(() => {
        api.updateCustodianForm(this.formId, json).then(() => {
          this.saveStatus = 'saved'
        }).catch((error) => {
          console.log(error)
          this.saveStatus = 'error'
        }).then(() => {
          if(this.saveStatus == 'saved' && close) {
            this.$router.push({ name: 'CustodianFeedbackDataset', params: { id: this.form.dataset_id }})
          }
        })
      }, 1000)
    },
    saveAndClose() {
      this.save(true)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .indent {
    padding-left: 2em;
  }

  .label {
/*    font-weight: normal;*/
  }

  label.required::after {
    content: "*";
    color: red;
  }

  aside.menu {
    position: sticky;
    display: inline-block;
    vertical-align: top;
    max-height: 100vh;
    overflow-y: auto;
    width: 200px;
    top: 0;
    bottom: 0;
    padding: 30px;
  }

  .radio-list label.radio {
    display: block;
    margin-left: 0;
    margin-bottom: 0.5em;
  }

  .field {
    margin-bottom: 2em;
  }

  section {
    counter-reset: question-counter;
  }
  .field.numbered {
    counter-increment: question-counter;
  }
  .field.numbered > label {
    text-indent: 2em hanging;
  }
  .field.numbered > label:before {
    width: 2em;
    display: inline-block;
    content: counter(question-counter) ". ";
  }

  /* Grey background for table headers */
  table.table thead tr {
     background: #eee;
  }
</style>

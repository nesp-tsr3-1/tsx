<template>
  <div class="section">
    <div class="feedback-home">
      <div class="columns">
        <div
          class="column is-2"
          style="border-right: 0.5px solid #eee;"
        >
          <div
            class="sticky-top"
            style="padding-top: 1.5em;"
          >
            <p class="menu-label">
              Contents
            </p>
            <ul
              ref="sideMenu"
              class="menu-list"
            >
              <li v-if="consentRequired">
                <a href="#consent_section">Conditions and consent</a>
              </li>
              <li v-if="showSection('citation')">
                <a href="#citation_section">Data citation and monitoring aims</a>
              </li>
              <li v-if="showSection('summary')">
                <a href="#summary_section">Data summary and processing</a>
              </li>
              <li v-if="showSection('statistics')">
                <a href="#statistics_section">Statistics and trend estimate</a>
              </li>
              <li>
                <a href="#suitability_section">Data suitability</a>
              </li>
              <li v-if="showSection('additional_comments_custodian')">
                <a href="#additional_comments_section">Additional comments</a>
              </li>
              <li v-if="showSection('funding_admin') || showSection('funding_custodian')">
                <a href="#funding_section">Monitoring program funding, logistics and governance (optional)</a>
              </li>
              <li v-if="showSection('additional_comments_admin')">
                <a href="#additional_comments_section">Additional comments</a>
              </li>
            </ul>
            <hr>
            <div class="buttons">
              <template v-if="viewOnly">
                <button
                  class="button is-primary"
                  @click="close"
                >
                  Close
                </button>
              </template>
              <template v-else>
                <button
                  class="button is-primary"
                  :disabled="!canSaveDraft"
                  @click="saveAndClose"
                >
                  {{ saveButtonLabel }}
                </button>
                <button
                  class="button is-primary"
                  :disabled="!canSubmit"
                  @click="submitAndClose"
                >
                  Submit
                </button>
              </template>
            </div>
            <p
              v-if="saveStatus == 'error'"
              class="help is-danger"
            >
              Failed to save form
            </p>
          </div>
        </div>
        <div class="column is-8">
          <user-nav />
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
                <h2 class="title">
                  {{ form.taxon.scientific_name }}
                </h2>
                <p class="content">
                  <span class="tag is-large">{{ form.dataset_id }}</span>
                </p>
              </div>
            </div>

            <div
              v-if="!viewOnly"
              class="notification is-warning"
            >
              <strong>Important:</strong> If you need to make any updates to your dataset, we recommend you do this before filling out this form. Updating your dataset will re-set and remove all drafted answers in this form and will archive all previously completed forms.
            </div>

            <div
              v-if="viewOnly && canEdit"
              class="notification is-warning sticky-top is-flex is-justify-content-space-between is-align-items-center"
              style="z-index: 10000"
            >
              <span>You are currently viewing this form in read-only mode.</span>
              <router-link
                :to="{
                  name: 'EditCustodianFeedbackForm',
                  params: { id: formId }}
                "
              >
                <button class="button is-primary">
                  Edit Form
                </button>
              </router-link>
            </div>

            <div
              v-if="viewOnly && !canEdit"
              class="notification is-warning sticky-top is-flex is-justify-content-space-between is-align-items-center"
              style="z-index: 10000"
            >
              <span>This form has been archived and cannot be edited.</span>
            </div>

            <hr>

            <fieldset :class="{ 'view-only': viewOnly }">
              <!-- Conditions and Consent -->
              <div v-if="consentRequired">
                <div
                  id="consent_section"
                  class="content"
                >
                  <h3>Conditions and consent</h3>
                  <p>
                    These feedback forms are based on the species monitoring data generously donated by you or your organisation as a data custodian for the development of Australia's Threatened Species Index. The index will allow for integrated reporting at national, state and regional levels, and track changes in threatened species populations. The goal of this feedback process is to inform decisions about which datasets will be included in the overall multi-species index. If custodians deem datasets to be unrepresentative of true species trends, these may be excluded from final analyses.
                  </p>
                  <p>
                    Within your individual datasets (see the ‘Datasets’ tab) you can access a clean version of your processed data in a (1) raw (confidential) and (2) aggregated format (to be made open to the public unless embargoed). For your aggregated data, please note that site names will be masked and spatial information on site locations will be denatured to the IBRA subregion centroids before making the data available to the public. We use the 'Living Planet Index' method to calculate trends (Collen et al. 2009) and follow their requirements on data when we assess suitability of data for trends.
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
                    This study adheres to the Guidelines of the ethical review process of The University of Queensland and the National Statement on Ethical Conduct in Human Research. Whilst you are free to discuss your participation in this study with project staff (Project Manager Tayla Lawrie: <a href="mailto:t.lawrie@uq.edu.au">t.lawrie@uq.edu.au</a> or <b>0476 378 354</b>), if you would like to speak to an officer of the University not involved in the study, you may contact the Ethics Coordinator on 07 3443 1656.
                  </p>
                  <p>
                    Your involvement in this elicitation process constitutes your consent for the Threatened Species Index team to use the information collected in research, subject to the information provided above. For more information about this expert elicitation process, please <a
                      href="/data/TSX_Custodian_Feedback_Participant_Information_Sheet_Sep24.pdf"
                      target="_blank"
                    >click here</a> to download our participant information sheet.
                  </p>
                  <p>
                    <b>References</b><br>
                    Collen, B., J. Loh, S. Whitmee, L. McRae, R. Amin, and J. E. Baillie. 2009. Monitoring change in vertebrate abundance: the living planet index. Conserv Biol 23:317-327.
                  </p>
                  <p>
                    <b>I have read and understood the conditions of the expert elicitation study for the project, “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species” and provide my consent.</b>
                  </p>
                </div>
                <div>
                  <div class="field">
                    <label class="checkbox required">
                      <input
                        v-model="formData.consent_given"
                        type="checkbox"
                      >
                      Agree
                    </label>
                  </div>
                  <div class="field">
                    <label class="label required">Please enter your name.</label>
                    <div class="control">
                      <input
                        v-model="formData.consent_name"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder=""
                      >
                    </div>
                  </div>
                </div>

                <div
                  v-if="consentLacking"
                  class="notification is-info is-light"
                >
                  <strong>To continue, first complete the consent form above.</strong>
                </div>

                <hr>
              </div>

              <fieldset :disabled="consentLacking">
                <!---- Admin Type ---->
                <div
                  v-if="isAdmin"
                  class="content"
                >
                  <div class="field">
                    <label class="label">In what format was the following survey data collected?</label>
                    <div class="control">
                      <div class="radio-list">
                        <label
                          v-for="option in options.admin_type"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.admin_type"
                            type="radio"
                            name="admin_type"
                            :value="option.id"
                            disabled
                          > {{ option.description }}
                        </label>
                      </div>
                    </div>
                    <button
                      v-if="formData.admin_type == 'informal'"
                      class="button block is-small"
                      @click="() => showAdminTypeDialog = true"
                    >
                      Switch to formal
                    </button>
                    <div class="notification">
                      For formal surveys, please add any “informal” comments to the relevant field(s) in this form. Please include your initials and the date when doing so.
                    </div>
                    <div
                      class="modal"
                      :class="{ 'is-active': showAdminTypeDialog }"
                    >
                      <div class="modal-background" />
                      <div class="modal-card">
                        <header class="modal-card-head">
                          <p class="modal-card-title">
                            Switch to formal survey
                          </p>
                        </header>
                        <section class="modal-card-body">
                          <p class="content">
                            Switching to a formal survey cannot be undone.
                          </p>
                          <p>Are you sure you wish to continue?</p>
                        </section>
                        <footer
                          class="modal-card-foot"
                          style="justify-content: right;"
                        >
                          <button
                            class="button is-primary"
                            @click="switchToFormal"
                          >
                            Switch
                          </button>
                          <button
                            class="button"
                            @click="() => showAdminTypeDialog = false"
                          >
                            Cancel
                          </button>
                        </footer>
                      </div>
                    </div>
                  </div>
                  <hr>
                </div>

                <!---- Data citation and monitoring aims ---->

                <template v-if="showSection('citation')">
                  <div
                    id="citation_section"
                    class="content"
                  >
                    <h3>Data citation and monitoring aims</h3>
                    <p>
                      <b>Data citation</b><br>
                      {{ citation }}
                    </p>
                  </div>

                  <div
                    v-if="showField('citation_agree')"
                    class="field numbered"
                  >
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Do you agree with the above suggested citation for your data? If no, please indicate how to correctly cite your data.</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian agree with the suggested citation? If no, what changes have they suggested to correctly cite their data?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.citation_agree"
                            type="radio"
                            name="citation_agree"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.citation_agree"
                        class="help is-danger"
                      >
                        {{ fieldErrors.citation_agree }}
                      </p>
                      <input
                        v-if="showField('citation_agree_comments')"
                        v-model="formData.citation_agree_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Suggested citation"
                      >
                      <p
                        v-if="fieldErrors.citation_agree_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.citation_agree_comments }}
                      </p>
                    </div>
                  </div>

                  <div
                    v-if="showField('monitoring_for_trend')"
                    class="field numbered"
                  >
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Has your monitoring program been explicitly designed to detect population trends over time? If no / unsure, please indicate the aims of your monitoring.</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Is the monitoring program explicitly designed to detect population trends over time? If no or unsure, what are the aims of their monitoring?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no_unsure"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.monitoring_for_trend"
                            type="radio"
                            name="monitoring_for_trend"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.monitoring_for_trend"
                        class="help is-danger"
                      >
                        {{ fieldErrors.monitoring_for_trend }}
                      </p>
                      <input
                        v-if="showField('monitoring_for_trend_comments')"
                        v-model="formData.monitoring_for_trend_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.monitoring_for_trend_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.monitoring_for_trend_comments }}
                      </p>
                    </div>
                  </div>

                  <div
                    v-if="showField('analyse_own_trends')"
                    class="field numbered"
                  >
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Do you analyse your own data for trends? If no, please indicate why.</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian analyse their own data for trends? If no, please indicate why.</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.analyse_own_trends"
                            type="radio"
                            name="analyse_own_trends"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.analyse_own_trends"
                        class="help is-danger"
                      >
                        {{ fieldErrors.analyse_own_trends }}
                      </p>
                      <input
                        v-if="showField('analyse_own_trends_comments')"
                        v-model="formData.analyse_own_trends_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.analyse_own_trends_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.analyse_own_trends_comments }}
                      </p>
                    </div>
                  </div>

                  <div
                    v-if="showField('pop_1750')"
                    class="field numbered"
                  >
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Can you estimate what percentage (%) of your species’ population existed in Australia at the start of your monitoring (assuming this was 100% in 1750)? <strong>This information is to help understand population baselines and determine whether the majority of a species' decline may have occurred prior to monitoring.</strong></label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >What has the custodian estimated to be the percentage (%) of the species’ population that existed in Australia at the start of the monitoring (assuming this was 100% in 1750)?</label>
                    <div class="control indent">
                      <input
                        v-model="formData.pop_1750"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter a percentage or 'Unsure'"
                      >
                      <p
                        v-if="fieldErrors.pop_1750"
                        class="help is-danger"
                      >
                        {{ fieldErrors.pop_1750 }}
                      </p>
                      <input
                        v-if="showField('pop_1750_comments')"
                        v-model="formData.pop_1750_comments"
                        class="input"
                        :readonly="viewOnly"
                        style="margin-top: 1em"
                        type="text"
                        placeholder="Additional comments"
                      >
                      <p
                        v-if="fieldErrors.pop_1750_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.pop_1750_comments }}
                      </p>
                    </div>
                  </div>
                </template>

                <!---- Data summary and processing ---->

                <template v-if="showSection('summary')">
                  <div
                    id="summary_section"
                    class="content"
                  >
                    <h3>Data summary and processing</h3>
                  </div>

                  <div class="columns">
                    <div class="column is-half">
                      <div
                        v-if="consistencyPlotAvailable"
                        class="content"
                      >
                        <canvas
                          ref="consistencyPlot"
                          style="height: 25em; max-height: 25em;"
                        />
                        <hr>
                        <p style="font-style: italic;">
                          The above dot plot shows the distribution of surveys at unique sites. Each row represents a time series in the dataset or data subset where a species/subspecies was monitored with a consistent method and unit of measurement at a single site over time. The maximum number of time-series included in this plot is 50.
                        </p>
                      </div>
                      <div
                        v-else
                        class="content"
                      >
                        Consistency plot unavailable
                      </div>
                    </div>
                    <div class="column is-half">
                      <div
                        v-if="intensityMapData"
                        class="content"
                      >
                        <div style="width: 100%; max-width: 640px; height: 25em; display: block; background: #eee;">
                          <HeatMap :heatmap-data="intensityMapData" />
                        </div>
                        <hr>
                        <p style="font-style: italic;">
                          The above map shows the location of your monitoring sites.
                        </p>
                      </div>
                      <div
                        v-else
                        class="content"
                      >
                        Map unavailable
                      </div>
                    </div>
                  </div>

                  <div class="content">
                    <table
                      v-if="form?.stats?.processing_summary"
                      class="table is-fullwidth is-striped is-bordered"
                    >
                      <thead>
                        <tr>
                          <th>
                            Search Type Description
                            <p class="content is-size-7 has-text-weight-normal">
                              (Monitoring method)
                            </p>
                          </th>
                          <th>Unit of Measurement</th>
                          <th>Unit Type</th>
                          <th>Data Processing Type</th>
                          <th>
                            Method of Aggregation
                            <p class="content is-size-7 has-text-weight-normal">
                              (How data were converted to an annual unit for the purpose of trend generation)
                            </p>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(row, rowIndex) in form.stats.processing_summary"
                          :key="rowIndex"
                        >
                          <td>{{ row.search_type }}</td>
                          <td>{{ row.unit }}</td>
                          <td>{{ row.unit_type }}</td>
                          <td>{{ row.data_processing_type }}</td>
                          <td>{{ row.aggregation_method }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div class="content">
                    <table
                      v-if="form?.stats?.site_management_summary"
                      class="table is-fullwidth is-striped is-bordered"
                    >
                      <thead>
                        <tr>
                          <th>Management Category</th>
                          <th>Management Comments</th>
                          <th>Number of Sites</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(row, rowIndex) in form.stats.site_management_summary"
                          :key="rowIndex"
                        >
                          <td>{{ row.management_category }}</td>
                          <td>{{ row.management_comments }}</td>
                          <td>{{ row.site_count.toLocaleString() }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div class="field numbered">
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Does the above data summary and plots appear representative of your dataset?</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian agree with the data summary? If no, what specifically do they disagree with?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.data_summary_agree"
                            type="radio"
                            name="data_summary_agree"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.data_summary_agree"
                        class="help is-danger"
                      >
                        {{ fieldErrors.data_summary_agree }}
                      </p>
                      <input
                        v-if="showField('data_summary_agree_comments')"
                        v-model="formData.data_summary_agree_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.data_summary_agree_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.data_summary_agree_comments }}
                      </p>
                    </div>
                  </div>

                  <div class="field numbered">
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Do you agree with how your data were handled? If no, please suggest an alternative method of aggregation.</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian agree with how the data were processed? If no, what alternative method of aggregation have they suggested?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no_unsure"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.processing_agree"
                            type="radio"
                            name="processing_agree"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.processing_agree"
                        class="help is-danger"
                      >
                        {{ fieldErrors.processing_agree }}
                      </p>
                      <input
                        v-if="showField('processing_agree_comments')"
                        v-model="formData.processing_agree_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.processing_agree_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.processing_agree_comments }}
                      </p>
                    </div>
                  </div>
                </template>

                <!---- Statistics and Trend Estimate ---->

                <template v-if="showSection('statistics')">
                  <div
                    id="statistics_section"
                    class="content"
                  >
                    <h3>Statistics and trend estimate</h3>
                  </div>

                  <div class="content">
                    <table class="table is-fullwidth is-striped is-bordered">
                      <thead>
                        <tr>
                          <th>Statistics (units)</th>
                          <th>Mean (±SD)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <template
                          v-for="(stats, statsIndex) in [form?.stats?.raw_data_stats].filter(x=>x)"
                          :key="statsIndex"
                        >
                          <tr>
                            <td colspan="2">
                              <b>Raw data</b>
                            </td>
                          </tr>
                          <tr>
                            <td>Period of monitoring (years)</td>
                            <td>{{ stats.min_year }}–{{ stats.max_year }}</td>
                          </tr>
                          <tr>
                            <td>Number of data points (surveys)</td>
                            <td>{{ stats.survey_count.toLocaleString() }}</td>
                          </tr>
                          <tr>
                            <td>Range of raw data (counts)</td>
                            <td>{{ stats.min_count.toLocaleString() }}–{{ stats.max_count.toLocaleString() }}</td>
                          </tr>
                          <tr>
                            <td>Number of 0 counts</td>
                            <td>{{ stats.zero_counts.toLocaleString() }}</td>
                          </tr>
                        </template>
                        <template
                          v-for="(stats, statsIndex) in [form?.stats?.time_series_stats].filter(x=>x)"
                          :key="statsIndex"
                        >
                          <tr>
                            <td colspan="2">
                              <b>Aggregated data</b>
                            </td>
                          </tr>
                          <tr>
                            <td>Number of repeatedly monitored sites (time series)</td>
                            <td>{{ stats.time_series_count.toLocaleString() }}</td>
                          </tr>
                          <tr>
                            <td>Time-series length (years)</td>
                            <td>
                              {{ formatDecimal(stats.time_series_length_mean) }}
                              (±{{ formatDecimal(stats.time_series_length_std) }})
                            </td>
                          </tr>
                          <tr>
                            <td>Time-series sample years (years)</td>
                            <td>
                              {{ formatDecimal(stats.time_series_sample_years_mean) }}
                              (±{{ formatDecimal(stats.time_series_sample_years_std) }})
                            </td>
                          </tr>
                          <tr>
                            <td>Time-series completeness (%)</td>
                            <td>
                              {{ formatDecimal(stats.time_series_completeness_mean) }}
                              (±{{ formatDecimal(stats.time_series_completeness_std) }})
                            </td>
                          </tr>
                          <tr>
                            <td>Time series sampling evenness (0 = very even sampling)</td>
                            <td>
                              {{ formatDecimal(stats.time_series_sampling_evenness_mean) }}
                              (±{{ formatDecimal(stats.time_series_sampling_evenness_std) }})
                            </td>
                          </tr>
                        </template>
                      </tbody>
                    </table>
                  </div>

                  <div
                    v-if="showField('statistics_agree')"
                    class="field numbered"
                  >
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Do the above statistics appear representative of your dataset?</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian agree with the data statistics (raw and aggregated)? If no, what specifically do they disagree with?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no_unsure"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.statistics_agree"
                            type="radio"
                            name="statistics_agree"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.statistics_agree"
                        class="help is-danger"
                      >
                        {{ fieldErrors.statistics_agree }}
                      </p>
                      <input
                        v-if="showField('statistics_agree_comments')"
                        v-model="formData.statistics_agree_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.statistics_agree_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.statistics_agree_comments }}
                      </p>
                    </div>
                  </div>

                  <hr>

                  <div
                    v-if="trendPlotAvailable"
                    id="trend-parameters"
                    class="card block"
                  >
                    <header class="card-header">
                      <p class="card-header-title">
                        <button
                          class="button"
                          @click="showTrendParameters = !showTrendParameters"
                        >
                          Customise trend
                        </button>
                      </p>
                    </header>
                    <div
                      v-if="showTrendParameters"
                      class="card-content"
                    >
                      <div class="columns">
                        <div class="column">
                          <div class="field">
                            <label class="label">Reference year</label>
                            <div class="control">
                              <div class="select">
                                <select v-model="trendParams.refYear">
                                  <option
                                    v-for="year in availableYears"
                                    :key="year"
                                    :value="year"
                                  >
                                    {{ year }}
                                  </option>
                                </select>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div class="column">
                          <div class="field">
                            <label class="label">Final year</label>
                            <div class="control">
                              <div class="select">
                                <select v-model="trendParams.finalYear">
                                  <option
                                    v-for="year in availableYears"
                                    :key="year"
                                    :value="year"
                                  >
                                    {{ year }}
                                  </option>
                                </select>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="content">
                        <div class="field">
                          <label class="label">Sites</label>
                          <div class="control">
                            <Multiselect
                              v-model="trendParams.sites"
                              mode="multiple"
                              :options="querySites"
                              :delay="500"
                              :searchable="true"
                              :close-on-select="false"
                              :filter-results="false"
                              no-options-text="No sites found"
                              placeholder="All sites"
                              label="name"
                              value-prop="id"
                              @open="(select) => select.refreshOptions()"
                            />
                          </div>
                          <div style="border-left: 2px solid #eee; padding-left: 1em; margin-top: 1em">
                            <table
                              v-if="trendParams.sites.length"
                              style="border: 1px solid #ccc;"
                              class="table is-narrow"
                            >
                              <thead>
                                <tr>
                                  <th>Site name</th>
                                  <th>Site ID</th>
                                  <th />
                                </tr>
                              </thead>
                              <tbody>
                                <tr
                                  v-for="(siteInfo, siteIndex) in trendParams.sites"
                                  :key="siteIndex"
                                >
                                  <td>{{ siteInfo.split(',')[1] }}</td>
                                  <td>{{ siteInfo.split(',')[0] }}</td>
                                  <td>
                                    <button
                                      class="delete is-small"
                                      style="margin-top: 4px"
                                      @click="deselectSite(siteInfo)"
                                    />
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                      <button
                        :disabled="trendStatus == 'processing'"
                        class="button is-dark"
                        @click="updateTrend"
                      >
                        Update Trend
                      </button>
                    </div>
                  </div>

                  <div
                    v-if="canResetTrend"
                    class="notification is-warning is-flex is-align-items-center is-justify-content-space-between"
                  >
                    <p><strong>Please note:</strong> you are not viewing the original trend in full</p>
                    <button
                      :disabled="trendStatus == 'processing'"
                      class="button is-dark"
                      @click="resetTrend"
                    >
                      Reset Trend
                    </button>
                  </div>

                  <div class="content">
                    <div
                      v-if="trendStatus == 'processing'"
                      style="margin-left: 1em;"
                    >
                      Loading <spinner
                        size="small"
                        style="display: inline-block;"
                      />
                    </div>
                    <div v-if="trendStatus == 'error'">
                      <p>An error occurred while generating the trend.</p>
                    </div>
                    <div v-if="trendStatus == 'empty'">
                      <p>Insufficient data available to generate a trend</p>
                    </div>
                    <div
                      v-if="trendPlotAvailable"
                      class="content"
                    >
                      <canvas
                        id="trend-plot"
                        ref="trendPlot"
                        style="height: 10em;"
                      />
                    </div>
                  </div>

                  <div
                    v-if="trendPlotAvailable"
                    class="content"
                  >
                    <hr>
                    <p style="font-style: italic;">
                      The above graph shows the estimated yearly change in relative abundance in relation to a baseline year where the index is set to 1. Changes are proportional - a value of 0.5 indicates the population is 50% below the baseline value; a value of 1.5 indicates 50% above baseline. The overall trend (mean value per year) is shown by the blue line - this line is used in the final multi-species TSX. The grey cloud indicates the uncertainty in the estimate as measured by the variability between all time series in your dataset. This trend excludes one-off surveys and absent-only time series.
                    </p>
                  </div>
                  <div
                    v-else
                    class="content"
                  >
                    <p style="font-style: italic;">
                      (Trend plot not available)
                    </p>
                    <hr>
                  </div>

                  <div class="field numbered">
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Do you agree with the trend estimate? If no or unsure, please elaborate (include detail on trends for specific sites where relevant).</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >Does the custodian agree with the trend? If no or unsure, what specifically do they disagree with?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no_unsure"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.trend_agree"
                            type="radio"
                            name="trend_agree"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.trend_agree"
                        class="help is-danger"
                      >
                        {{ fieldErrors.trend_agree }}
                      </p>
                      <input
                        v-if="showField('trend_agree_comments')"
                        v-model="formData.trend_agree_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.trend_agree_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.trend_agree_comments }}
                      </p>
                    </div>
                  </div>

                  <div class="field numbered">
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Looking at the trend for your data, what should be the reference year at which the index should start?</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >What reference year has the custodian suggested for their trend?</label>
                    <div class="control indent">
                      <input
                        v-model="formData.start_year"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.start_year"
                        class="help is-danger"
                      >
                        {{ fieldErrors.start_year }}
                      </p>
                      <input
                        v-if="showField('start_year_comments')"
                        v-model="formData.start_year_comments"
                        class="input"
                        :readonly="viewOnly"
                        style="margin-top:1em;"
                        type="text"
                        placeholder="Additional comments"
                      >
                      <p
                        v-if="fieldErrors.start_year_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.start_year_comments }}
                      </p>
                    </div>
                  </div>

                  <div class="field numbered">
                    <label
                      v-if="notAdmin"
                      class="label required"
                    >Looking at the trend for your data, what should be the year at which the index should end?</label>
                    <label
                      v-if="isAdmin"
                      class="label"
                    >What end year has the custodian suggested for their trend?</label>
                    <div class="control indent">
                      <input
                        v-model="formData.end_year"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.end_year"
                        class="help is-danger"
                      >
                        {{ fieldErrors.end_year }}
                      </p>
                      <input
                        v-if="showField('end_year_comments')"
                        v-model="formData.end_year_comments"
                        class="input"
                        :readonly="viewOnly"
                        style="margin-top:1em;"
                        type="text"
                        placeholder="Additional comments"
                      >
                      <p
                        v-if="fieldErrors.end_year_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.end_year_comments }}
                      </p>
                    </div>
                  </div>
                </template>

                <!---- Data suitability ---->

                <template v-if="showSection('suitability')">
                  <div
                    id="suitability_section"
                    class="content"
                  >
                    <h3>Data suitability</h3>
                  </div>

                  <div class="content">
                    <p>
                      The below fields relate to the suitability of your data for demonstrating trends in populations over time. After reading the descriptions, please select the most suitable option.
                    </p>
                    <table class="table is-fullwidth is-striped is-bordered">
                      <thead>
                        <tr>
                          <th>Suitability criteria</th>
                          <th>Description</th>
                          <th colspan="3">
                            Your assessment
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td :rowspan="options.standardisation_of_method_effort.length + 1">
                            <div class="field numbered">
                              <label
                                class="label"
                                :class="{ required: !isAdmin }"
                              >Standardisation of method effort</label>
                              <p
                                v-if="fieldErrors.standardisation_of_method_effort"
                                class="help is-danger"
                              >
                                {{ fieldErrors.standardisation_of_method_effort }}
                              </p>
                            </div>
                          </td>
                          <td :rowspan="options.standardisation_of_method_effort.length + 1">
                            This data suitability indicator rates the degree of standardisation of monitoring method/effort and is assessed to the data source level by enquiring with the data custodian and examining data.
                          </td>
                        </tr>
                        <tr
                          v-for="option in options.standardisation_of_method_effort"
                          :key="option.id"
                          @click="() => { formData.standardisation_of_method_effort = option.id}"
                        >
                          <td>
                            <input
                              v-model="formData.standardisation_of_method_effort"
                              type="radio"
                              name="standardisation_of_method_effort"
                              :value="option.id"
                            >
                          </td>
                          <td>{{ option.id }}</td>
                          <td>{{ option.description }}</td>
                        </tr>

                        <tr>
                          <td :rowspan="options.objective_of_monitoring.length + 1">
                            <div class="field numbered">
                              <label
                                class="label"
                                :class="{ required: !isAdmin }"
                              >Objective of monitoring</label>
                              <p
                                v-if="fieldErrors.objective_of_monitoring"
                                class="help is-danger"
                              >
                                {{ fieldErrors.objective_of_monitoring }}
                              </p>
                            </div>
                          </td>
                          <td :rowspan="options.objective_of_monitoring.length + 1">
                            This field indicates the objective of the monitoring.
                          </td>
                        </tr>
                        <tr
                          v-for="option in options.objective_of_monitoring"
                          :key="option.id"
                          @click="() => { formData.objective_of_monitoring = option.id}"
                        >
                          <td>
                            <input
                              v-model="formData.objective_of_monitoring"
                              type="radio"
                              name="objective_of_monitoring"
                              :value="option.id"
                            >
                          </td>
                          <td>{{ option.id }}</td>
                          <td>{{ option.description }}</td>
                        </tr>

                        <tr>
                          <td :rowspan="options.consistency_of_monitoring.length + 1">
                            <div class="field numbered">
                              <label
                                class="label"
                                :class="{ required: !isAdmin }"
                              >Consistency of monitoring</label>
                              <p
                                v-if="fieldErrors.consistency_of_monitoring"
                                class="help is-danger"
                              >
                                {{ fieldErrors.consistency_of_monitoring }}
                              </p>
                            </div>
                          </td>
                          <td :rowspan="options.consistency_of_monitoring.length + 1">
                            This data suitability indicator rates the degree of consistency by which the same sites were repeatedly monitored over time.
                          </td>
                        </tr>
                        <tr
                          v-for="option in options.consistency_of_monitoring"
                          :key="option.id"
                          @click="() => { formData.consistency_of_monitoring = option.id}"
                        >
                          <td>
                            <input
                              v-model="formData.consistency_of_monitoring"
                              type="radio"
                              name="consistency_of_monitoring"
                              :value="option.id"
                            >
                          </td>
                          <td>{{ option.id }}</td>
                          <td>{{ option.description }}</td>
                        </tr>

                        <tr>
                          <td :rowspan="options.monitoring_frequency_and_timing.length + 1">
                            <div class="field numbered">
                              <label
                                class="label"
                                :class="{ required: !isAdmin }"
                              >Monitoring frequency and timing</label>
                              <p
                                v-if="fieldErrors.monitoring_frequency_and_timing"
                                class="help is-danger"
                              >
                                {{ fieldErrors.monitoring_frequency_and_timing }}
                              </p>
                            </div>
                          </td>
                          <td :rowspan="options.monitoring_frequency_and_timing.length + 1">
                            This data suitability indicator rates whether the taxon was monitored with an appropriate frequency and during an appropriate season/timing.
                          </td>
                        </tr>
                        <tr
                          v-for="option in options.monitoring_frequency_and_timing"
                          :key="option.id"
                          @click="() => { formData.monitoring_frequency_and_timing = option.id}"
                        >
                          <td>
                            <input
                              v-model="formData.monitoring_frequency_and_timing"
                              type="radio"
                              name="monitoring_frequency_and_timing"
                              :value="option.id"
                            >
                          </td>
                          <td>{{ option.id }}</td>
                          <td>{{ option.description }}</td>
                        </tr>

                        <tr>
                          <td :rowspan="options.absences_recorded.length + 1">
                            <div class="field numbered">
                              <label
                                class="label"
                                :class="{ required: !isAdmin }"
                              >Were absences recorded systematically?</label>
                              <p
                                v-if="fieldErrors.absences_recorded"
                                class="help is-danger"
                              >
                                {{ fieldErrors.absences_recorded }}
                              </p>
                            </div>
                          </td>
                          <td :rowspan="options.absences_recorded.length + 1">
                            Absences are non-detections of taxa i.e. where 0 counts of a species are recorded.
                          </td>
                        </tr>
                        <tr
                          v-for="option in options.absences_recorded"
                          :key="option.id"
                          @click="() => { formData.absences_recorded = option.id}"
                        >
                          <td>
                            <input
                              v-model="formData.absences_recorded"
                              type="radio"
                              name="absences_recorded"
                              :value="option.id"
                            >
                          </td>
                          <td colspan="2">
                            {{ option.description }}
                          </td>
                        </tr>
                      </tbody>
                    </table>

                    <div class="field">
                      <label
                        v-if="notAdmin"
                        class="label"
                      >Please add any additional comments on data suitability and the criteria below.</label>
                      <label
                        v-if="isAdmin"
                        class="label"
                      >What additional comments on data suitability and the criteria has the custodian provided?</label>
                      <div class="control">
                        <input
                          v-model="formData.data_suitability_comments"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                      </div>
                    </div>
                  </div>
                </template>

                <!-- Additional comments -->

                <template v-if="showSection('additional_comments_custodian')">
                  <div
                    id="additional_comments_section"
                    class="content"
                  >
                    <h3>Additional comments</h3>
                  </div>

                  <div
                    v-if="showField('additional_comments')"
                    class="field"
                  >
                    <label class="label">Please provide any additional comments about this dataset and/or trend below.</label>
                    <div class="control">
                      <textarea
                        v-model="formData.additional_comments"
                        class="textarea"
                        placeholder="Enter your answer"
                      />
                    </div>
                  </div>
                </template>

                <!-- Monitoring program funding, logistics and governance -->

                <template v-if="showSection('funding_admin')">
                  <div
                    id="funding_section"
                    class="content"
                  >
                    <h3>Monitoring program funding, logistics and governance</h3>
                  </div>

                  <div class="field numbered">
                    <label class="label">Has the custodian answered the optional questions about funding, logistics and governance?</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.yes_no"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.cost_data_provided"
                            type="radio"
                            name="cost_data_provided"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                      <p
                        v-if="fieldErrors.cost_data_provided"
                        class="help is-danger"
                      >
                        {{ fieldErrors.cost_data_provided }}
                      </p>
                    </div>
                  </div>

                  <div class="field numbered">
                    <label class="label">Where the custodian has provided funding data, what value have they estimated as the total investment in the dataset to date (not counting in-kind support)?</label>
                    <div class="control indent">
                      <input
                        v-model="formData.estimated_cost_dataset"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter value or type 'unsure'"
                      >
                      <p
                        v-if="fieldErrors.estimated_cost_dataset"
                        class="help is-danger"
                      >
                        {{ fieldErrors.estimated_cost_dataset }}
                      </p>
                    </div>
                  </div>

                  <div class="field numbered">
                    <label class="label">Please add any additional comments from the custodian about the monitoring program below.</label>
                    <div class="control indent">
                      <input
                        v-model="formData.cost_data_provided_comments"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter your answer"
                      >
                      <p
                        v-if="fieldErrors.cost_data_provided_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.cost_data_provided_comments }}
                      </p>
                    </div>
                  </div>
                </template>

                <template v-if="showSection('additional_comments_admin')">
                  <div
                    id="additional_comments_section"
                    class="content"
                  >
                    <h3>Additional comments</h3>
                  </div>

                  <div class="field">
                    <label class="label">Please add any additional comments from the custodian below.</label>
                    <div class="control">
                      <textarea
                        v-model="formData.custodian_comments"
                        class="textarea"
                        type="text"
                        placeholder="Enter your answer"
                      />
                      <p
                        v-if="fieldErrors.custodian_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.custodian_comments }}
                      </p>
                    </div>
                  </div>

                  <div class="field">
                    <label class="label">INTERNAL ONLY: Please add any additional comments on the dataset below. Include your initials and date where possible.</label>
                    <div class="control">
                      <textarea
                        v-model="formData.internal_comments"
                        class="textarea"
                        type="text"
                        placeholder="Enter your answer"
                      />
                      <p
                        v-if="fieldErrors.internal_comments"
                        class="help is-danger"
                      >
                        {{ fieldErrors.internal_comments }}
                      </p>
                    </div>
                  </div>
                </template>

                <template v-if="showSection('funding_custodian')">
                  <div
                    id="funding_section"
                    class="content"
                  >
                    <h3>Monitoring program funding, logistics and governance</h3>
                  </div>

                  <p class="content">
                    Questions 17 to 32 below are optional. We hope you are interested in providing some further information about your monitoring program.
                  </p>

                  <div class="field numbered">
                    <label class="label">Please indicate if you would prefer to provide this information via a phone or video call with our project team:</label>
                    <div class="control indent">
                      <div class="radio-list">
                        <label
                          v-for="option in options.monitoring_program_information_provided"
                          :key="option.id"
                          class="radio"
                        >
                          <input
                            v-model="formData.monitoring_program_information_provided"
                            type="radio"
                            name="monitoring_program_information_provided"
                            :value="option.id"
                          > {{ option.description }}
                        </label>
                      </div>
                    </div>
                  </div>

                  <div
                    v-if="formData.monitoring_program_information_provided == 'please_contact'"
                    class="field"
                  >
                    <div class="control indent">
                      <input
                        v-model="formData.monitoring_program_information_contact"
                        class="input"
                        :readonly="viewOnly"
                        type="text"
                        placeholder="Enter contact phone number or email address"
                      >
                    </div>
                  </div>

                  <div
                    v-if="showPreviousAnswersMenu && previousAnswers.length > 0"
                    class="field has-addons"
                  >
                    <div class="control indent">
                      <div class="select">
                        <select v-model="selectedPreviousAnswer">
                          <option :value="null">
                            Select form…
                          </option>
                          <option
                            v-for="option in previousAnswers"
                            :key="option.id"
                            :value="option.id"
                          >
                            {{ option.description }}
                          </option>
                        </select>
                      </div>
                    </div>
                    <div class="control">
                      <button
                        class="button is-dark"
                        :disabled="disableCopyAnswersButton"
                        @click="copyAnswers"
                      >
                        {{ copyAnswersButtonLabel }}
                      </button>
                    </div>
                  </div>
                  <div
                    v-if="showPreviousAnswersMenu && previousAnswers.length == 0"
                    class="notification"
                  >
                    No previously submitted answers found for this dataset.
                  </div>
                  <hr>

                  <div
                    v-if="disableMonitoringProgramFields"
                    class="notification is-info is-light"
                  >
                    <strong>To fill out the following fields, first answer question 16 above.</strong>
                  </div>

                  <fieldset :disabled="disableMonitoringProgramFields">
                    <div class="field numbered">
                      <label class="label">Effort: How much time on average per year was spent on project labour, i.e. data collection in the field? </label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a. Days/year paid labour:</label>
                          <div>
                            <input
                              v-model="formData.effort_labour_paid_days_per_year"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_labour_paid_days_per_year"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_labour_paid_days_per_year }}
                            </p>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Days/year volunteered time:</label>
                          <div>
                            <input
                              v-model="formData.effort_labour_volunteer_days_per_year"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_labour_volunteer_days_per_year"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_labour_volunteer_days_per_year }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Effort: How much time on average per year was spent on project overheads, e.g. data collation and dataset maintenance? </label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a. Days/year paid labour:</label>
                          <div>
                            <input
                              v-model="formData.effort_overheads_paid_days_per_year"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_overheads_paid_days_per_year"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_overheads_paid_days_per_year }}
                            </p>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Days/year volunteered time:</label>
                          <div>
                            <input
                              v-model="formData.effort_overheads_volunteer_days_per_year"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_overheads_volunteer_days_per_year"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_overheads_volunteer_days_per_year }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Effort: Approximately how many people were involved in the last bout of monitoring (including both field and office work)</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a. Paid staff:</label>
                          <div>
                            <input
                              v-model="formData.effort_paid_staff_count"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_paid_staff_count"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_paid_staff_count }}
                            </p>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Volunteers:</label>
                          <div>
                            <input
                              v-model="formData.effort_volunteer_count"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.effort_volunteer_count"
                              class="help is-danger"
                            >
                              {{ fieldErrors.effort_volunteer_count }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Funding: How much do you think in AUD$ a single survey costs (not counting in-kind support)?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.funding_cost_per_survey_aud"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                        <p
                          v-if="fieldErrors.funding_cost_per_survey_aud"
                          class="help is-danger"
                        >
                          {{ fieldErrors.funding_cost_per_survey_aud }}
                        </p>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Funding: Can you estimate in AUD$ the total investment in the dataset to date (again not counting in-kind support)?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.funding_total_investment_aud"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                        <p
                          v-if="fieldErrors.funding_total_investment_aud"
                          class="help is-danger"
                        >
                          {{ fieldErrors.funding_total_investment_aud }}
                        </p>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Funding: Who has been paying for the monitoring? (e.g. government grants, research funds, private donations etc. – list multiple funding sources if they have been needed over the years)</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a. Government grants:</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.funding_source_government_grants"
                              class="radio"
                              type="radio"
                              name="funding_source_government_grants"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.funding_source_government_grants"
                              class="radio"
                              type="radio"
                              name="funding_source_government_grants"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Research funds:</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.funding_source_research_funds"
                              class="radio"
                              type="radio"
                              name="funding_source_research_funds"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.funding_source_research_funds"
                              class="radio"
                              type="radio"
                              name="funding_source_research_funds"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>c. Private donations:</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.funding_source_private_donations"
                              class="radio"
                              type="radio"
                              name="funding_source_private_donations"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.funding_source_private_donations"
                              class="radio"
                              type="radio"
                              name="funding_source_private_donations"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>d. Other:</label>
                          <input
                            v-model="formData.funding_source_other"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                        <div class="subfield">
                          <label>e. Can you estimate the total number of funding sources so far?:</label>
                          <div>
                            <input
                              v-model="formData.funding_source_count"
                              class="input"
                              :readonly="viewOnly"
                              type="text"
                              placeholder="Enter your answer"
                            >
                            <p
                              v-if="fieldErrors.funding_source_count"
                              class="help is-danger"
                            >
                              {{ fieldErrors.funding_source_count }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Leadership: Who has been providing the drive to keep the monitoring going after the baseline was established?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.leadership"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Impact: Are data being used to directly inform management of the threatened species or measure the effectiveness of management actions? </label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.impact_used_for_management"
                              class="radio"
                              type="radio"
                              name="impact_used_for_management"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.impact_used_for_management"
                              class="radio"
                              type="radio"
                              name="impact_used_for_management"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.impact_used_for_management_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Impact: Is your organisation responsible for managing this species in the monitored area?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.impact_organisation_responsible"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Impact: Can you describe any management that has changed because of the monitoring?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.impact_management_changes"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Data availability: Is your monitoring data readily available to the public (e.g. through reports, or on website). If not, can the public access it?</label>
                      <div class="control indent">
                        <input
                          v-model="formData.data_availability"
                          class="input"
                          :readonly="viewOnly"
                          type="text"
                          placeholder="Enter your answer"
                        >
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Succession: Do you have commitments to extend the monitoring into the future? </label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.succession_commitment"
                              class="radio"
                              type="radio"
                              name="succession_commitment"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.succession_commitment"
                              class="radio"
                              type="radio"
                              name="succession_commitment"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.succession_commitment_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Succession: Have you developed a plan for continual monitoring when the current organisers/you need to stop?</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.succession_plan"
                              class="radio"
                              type="radio"
                              name="succession_plan"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.succession_plan"
                              class="radio"
                              type="radio"
                              name="succession_plan"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.succession_plan_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Design: Was there thought about the statistical power of the monitoring when it was started (i.e. the probability that change could be detected?)</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.design_statistical_power"
                              class="radio"
                              type="radio"
                              name="design_statistical_power"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.design_statistical_power"
                              class="radio"
                              type="radio"
                              name="design_statistical_power"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.design_statistical_power_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Design: Is anything other than the numbers of threatened species being monitored at the same time that could explain changes in abundance (e.g. prevalence of a threat, fire, breeding success, etc?)</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.design_other_factors"
                              class="radio"
                              type="radio"
                              name="design_other_factors"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.design_other_factors"
                              class="radio"
                              type="radio"
                              name="design_other_factors"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.design_other_factors_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>

                    <div class="field numbered">
                      <label class="label">Co-benefits: Is the monitoring program for this species also collecting trend information on other threatened species?</label>
                      <div class="control indent">
                        <div class="subfield">
                          <label>a.</label>
                          <div class="horizontal-radio-list">
                            <label><input
                              v-model="formData.co_benefits_other_species"
                              class="radio"
                              type="radio"
                              name="co_benefits_other_species"
                              value="yes"
                            > Yes</label>
                            <label><input
                              v-model="formData.co_benefits_other_species"
                              class="radio"
                              type="radio"
                              name="co_benefits_other_species"
                              value="no"
                            > No</label>
                          </div>
                        </div>
                        <div class="subfield">
                          <label>b. Please expand:</label>
                          <input
                            v-model="formData.co_benefits_other_species_comments"
                            class="input"
                            :readonly="viewOnly"
                            type="text"
                            placeholder="Enter your answer"
                          >
                        </div>
                      </div>
                    </div>
                  </fieldset>
                </template>
              </fieldset>
            </fieldset>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { formatDateTime, setupPageNavigationHighlighting } from '../util.js'
import { generateCitation } from '../util.js'
import { plotConsistency } from '../plotConsistency.js'
import { plotTrend, generateTrendPlotData } from '../plotTrend.js'
import HeatMap from './HeatMap.vue'
import Multiselect from '@vueform/multiselect'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'

export default {
  name: 'CustodianFeedbackForm',
  components: {
    HeatMap,
    Multiselect,
    Spinner
  },
  props: {
    viewOnly: Boolean
  },
  data() {
    return {
      currentUser: null,
      status: 'loading',
      saveStatus: 'none',
      formId: this.$route.params.id,
      form: null,
      formData: {

      },
      fieldErrors: {},
      options: null,
      formDefinition: null,
      showAdminTypeDialog: false,

      previousAnswers: [],
      selectedPreviousAnswer: null,
      copyAnswerStatus: 'idle',

      showTrendParameters: false,
      trendParams: {
        sites: [],
        refYear: null,
        finalYear: null
      },
      trendStatus: 'ready',
      canResetTrend: false,
      currentTrendPlot: null
    }
  },
  computed: {
    citation() {
      let source = this.form.source
      return source && generateCitation(source.authors, source.details, source.provider)
    },
    isAdmin() {
      return this.form && this.form.feedback_type.code === 'admin'
    },
    notAdmin() {
      return this.form.feedback_type.code !== 'admin'
    },
    formJSON() {
      return JSON.stringify(this.formData, null, 4)
    },
    saveButtonLabel() {
      if(this.saveStatus == 'saving') {
        return 'Saving…'
      } else {
        return 'Save Draft and Close'
      }
    },
    canSaveDraft() {
      return this.saveStatus != 'saving'
    },
    canSubmit() {
      return this.saveStatus != 'saving'
    },
    consistencyPlotAvailable() {
      return !!this.form?.stats?.monitoring_consistency
    },
    intensityMapData() {
      return this.form?.stats?.intensity_map
    },
    trendPlotAvailable() {
      return !!this.form?.stats?.trend
    },
    showMonitoringProgramFields() {
      return this.notAdmin
    },
    disableMonitoringProgramFields() {
      let x = this.formData.monitoring_program_information_provided
      return !(x == 'provided' || x == 'provided_copy')
    },
    showPreviousAnswersMenu() {
      return this.formData.monitoring_program_information_provided == 'provided_copy'
    },
    disableCopyAnswersButton() {
      return this.selectedPreviousAnswer == null || this.copyAnswerStatus != 'idle'
    },
    copyAnswersButtonLabel() {
      return this.copyAnswerStatus == 'idle' ? 'Copy Answers' : 'Copying…'
    },
    consentRequired() {
      return !this.currentUser?.is_admin
    },
    consentGiven() {
      return this.formData?.consent_given
    },
    consentLacking() {
      return this.consentRequired && !this.consentGiven
    },
    availableYears() {
      let stats = this.form?.stats?.raw_data_stats
      if(stats) {
        let min = stats.min_year
        let max = stats.max_year
        return Array.from({ length: max - min + 1 }, (x, i) => i + min)
      } else {
        return []
      }
    },
    canEdit() {
      return ['incomplete', 'draft', 'complete'].includes(this.form.feedback_status.code)
    },
    consistencyPlotVisible() {
      return this.consistencyPlotAvailable && this.showSection('summary')
    }
  },
  watch: {
    consistencyPlotVisible(isVisible) {
      let data = this.form?.stats?.monitoring_consistency
      if(isVisible && data) {
        this.$nextTick(() => {
          plotConsistency(data, this.$refs.consistencyPlot)
        })
      }
    },
    formData: {
      deep: true,
      handler() {
        if(this.viewOnly && !this.ignoreNextFormDataUpdate) {
          setTimeout(() => {
            this.ignoreNextFormDataUpdate = true
            this.formData = structuredClone(this.initialFormData)
          })
        } else {
          this.ignoreNextFormDataUpdate = false
        }
      }
    }
  },
  created() {
    api.custodianFeedbackFormDefinition().then((formDefinition) => {
      this.formDefinition = formDefinition
      this.options = formDefinition.options
      this.refresh()
    })
    api.isLoggedIn().then((isLoggedIn) => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })

    api.currentUser().then((currentUser) => {
      this.currentUser = currentUser
    }).catch((error) => {
      this.error = error
    })
  },
  mounted() {
    this.disposables = []
    this.setupSideMenu()
  },
  unmounted() {
    for(let f of this.disposables) {
      f()
    }
  },
  methods: {
    refresh() {
      api.custodianFeedbackForm(this.formId).then((form) => {
        this.form = form

        let initialFormData = {
          ...form.answers,
          admin_type: form.answers.admin_type || 'informal'
        }

        this.formData = initialFormData
        this.initialFormData = structuredClone(initialFormData)

        this.trendParams.refYear = form?.stats?.raw_data_stats?.min_year
        this.trendParams.finalYear = form?.stats?.raw_data_stats?.max_year

        if(this.trendPlotAvailable) {
          this.plotTrend(form?.stats?.trend)
        }

        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        console.log(error.json)
        this.status = 'error'
      })
      api.custodianFeedbackPreviousAnswers(this.formId).then(answers => this.previousAnswers = answers)
    },
    formatDateTime,
    formatDecimal(x) {
      return x.toLocaleString(undefined, { maximumFractionDigits: 2 })
    },
    save(close, submit) {
      let json = { ...this.formData }
      if(submit) {
        json.action = 'submit'
      }
      this.saveStatus = 'saving'
      setTimeout(() => {
        api.updateCustodianForm(this.formId, json).then(() => {
          this.saveStatus = 'saved'
        }).catch((error) => {
          if(error.json) {
            this.fieldErrors = error.json
            setTimeout(() => {
              document.querySelector('.field .help.is-danger')?.closest('.field')?.scrollIntoView()
            })
          }
          this.saveStatus = 'error'
        }).then(() => {
          if(this.saveStatus == 'saved' && close) {
            this.close()
          }
        })
      }, 1000)
    },
    saveAndClose() {
      this.save(true)
    },
    submitAndClose() {
      this.save(true, true)
    },
    close() {
      this.$router.push({ name: 'CustodianFeedbackDataset', params: { id: this.form.dataset_id } })
    },
    setupSideMenu() {
      let highlighter = setupPageNavigationHighlighting(this.$refs.sideMenu)
      this.disposables.push(() => highlighter.dispose())
    },
    showField(fieldName) {
      if(fieldName.endsWith('_comments')) {
        let parentFieldName = fieldName.replace(/_comments$/, '')
        let parentFieldValue = this.formData[parentFieldName] ?? ''
        return this.isAdmin || ['no', 'unsure'].includes(parentFieldValue.toLowerCase())
      }

      if(this.isAdmin && this.formData.admin_type == 'informal') {
        let informalFields = [
          'trend_agree',
          'trend_agree_comments',
          'start_year',
          'start_year_comments',
          'end_year',
          'end_year_comments',
          'custodian_comments',
          'internal_comments'
        ]
        return informalFields.includes(fieldName)
      }

      return true
    },
    showSection(sectionName) {
      if(this.form && this.isAdmin && this.formData.admin_type == 'informal') {
        let informalSections = [
          'citation',
          'statistics',
          'additional_comments_admin'
        ]
        return informalSections.includes(sectionName)
      } else if(sectionName.endsWith('_admin')) {
        return this.isAdmin
      } else if(sectionName.endsWith('_custodian')) {
        return !this.isAdmin
      } else {
        return true
      }
    },
    switchToFormal() {
      this.formData.admin_type = 'formal'
      this.showAdminTypeDialog = false
    },
    copyAnswers() {
      this.copyAnswerStatus = 'loading'
      api.custodianFeedbackForm(this.selectedPreviousAnswer).then((formData) => {
        let fieldNames = this.formDefinition.fields.map(f => f.name)
        let index = fieldNames.indexOf('monitoring_program_information_provided')
        for(let field of fieldNames.slice(index + 1)) {
          this.formData[field] = formData.answers[field]
        }
      }).finally(() => {
        this.copyAnswerStatus = 'idle'
      })
    },
    querySites(query) {
      if(!this.form) {
        return []
      }

      let params = {
        source_id: this.form.source.id,
        taxon_id: this.form.taxon.id
      }
      return api.dataSubsetSites(params)
        .then(sites => sites.map(site => ({ name: site.name, id: site.id + ',' + site.name })))
    },
    deselectSite(site) {
      this.trendParams.sites = this.trendParams.sites.filter(x => x != site)
    },
    updateTrend() {
      this.currentTrendPlot?.destroy()
      let params = {
        source_id: this.form.source.id,
        taxon_id: this.form.taxon.id,
        reference_year: this.trendParams.refYear,
        final_year: this.trendParams.finalYear
      }
      if(this.trendParams.sites.length) {
        params.site_id = this.trendParams.sites.map(x => x.split(',')[0]).join(',')
      }
      api.dataSubsetGenerateTrend(params).then((trend) => {
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrend(trend.id), 3000)
      }).catch((e) => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    checkTrend(id) {
      api.dataSubsetTrendStatus(id).then((status) => {
        if(status.status == 'ready') {
          api.dataSubsetTrend(id).then((data) => {
            let plotData = generateTrendPlotData(data)
            let isEmpty = plotData.labels.length < 2
            if(isEmpty) {
              this.trendStatus = 'empty'
            } else {
              this.plotTrend(data)
            }
            this.canResetTrend = true
          })
        } else if(status.status == 'processing') {
          setTimeout(() => this.checkTrend(id), 2000)
        }
      }).catch((e) => {
        console.log(e)
        this.trendStatus = 'error'
        this.canResetTrend = true
      })
    },
    resetTrend() {
      this.trendParams.sites = []
      this.trendParams.refYear = this.form?.stats?.raw_data_stats?.min_year
      this.trendParams.finalYear = this.form?.stats?.raw_data_stats?.max_year
      this.canResetTrend = false
      this.plotTrend(this.form?.stats?.trend)
    },
    plotTrend(data) {
      this.trendStatus = 'ready'
      this.currentTrendPlot?.destroy()
      setTimeout(() => {
        this.currentTrendPlot = plotTrend(data, this.$refs.trendPlot)
      })
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

  .sticky-top {
    position: sticky;
    top: 0;
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

  .menu-list a.current {
    font-weight: bold;
  }

  .radio-list label.radio {
    display: block;
    margin-left: 0;
    margin-bottom: 0.5em;
  }

  .horizontal-radio-list label {
    margin-right: 1em;
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

  div.subfield {
    display: flex;
    align-items: baseline;
    margin-bottom: 0.5em;
  }

  div.subfield > *:first-child {
    flex-grow: 1;
    flex-shrink: 0;
    flex-basis: 0;
  }
  div.subfield > *:nth-child(2) {
    flex-grow: 3;
    flex-shrink: 1;
    flex-basis: 0;
  }

  fieldset[disabled] {
    opacity: 0.7;
  }

  /* Disable pointer events on most inputs when in view-only mode */
  fieldset.view-only .radio,
  fieldset.view-only .select,
  fieldset.view-only .checkbox,
  fieldset.view-only tr {
    pointer-events: none;
  }
</style>
<style src="@vueform/multiselect/themes/default.css"></style>

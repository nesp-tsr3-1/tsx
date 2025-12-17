<template>
  <slot name="criteria-title" />
  <fieldset
    class="block"
    :disabled="submitting"
    :class="{ sideborder: sourceId }"
  >
    <div
      v-if="enableStateFilter"
      class="field"
    >
      <label class="label">State/Territory</label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.state">
            <option
              :value="null"
              selected
            >
              All States and Territories
            </option>
            <option
              v-for="state in options.state"
              :key="state"
              :value="state"
            >
              {{ state }}
            </option>
          </select>
        </div>
      </div>
    </div>
    <div
      v-if="enableRegionFilter"
      class="field"
      data-test="region-filter"
    >
      <label class="label">Regions</label>
      <div class="control">
        <Multiselect
          v-model="criteria.regions"
          mode="multiple"
          :options="queryRegions"
          :searchable="true"
          no-options-text="No regions found"
          placeholder="All regions"
          label="label"
          value-prop="id"
          @open="(select) => select.refreshOptions()"
        />
      </div>
      <div style="border-left: 2px solid #eee; padding-left: 1em; margin-top: 1em">
        <table
          v-if="criteria.regions.length"
          style="border: 1px solid #ccc;"
          class="table is-narrow"
        >
          <thead>
            <tr>
              <th>Region</th>
              <th>State</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(region, index) in criteria.regions"
              :key="index"
            >
              <td>{{ regionById(region).name }}</td>
              <td>{{ regionById(region).state }}</td>
              <td>
                <button
                  class="delete is-small"
                  style="margin-top: 4px"
                  @click="deselectRegion(region)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div
      v-if="enableProgramFilter"
      class="field"
      data-test="program-filter"
    >
      <label class="label">Programs</label>
      <div class="control">
        <Multiselect
          v-model="criteria.monitoringPrograms"
          mode="tags"
          :options="options.monitoringPrograms"
          :searchable="true"
          :can-clear="canAccessAllPrograms"
          no-options-text="No programs found"
          placeholder="Any or no program"
          label="description"
          value-prop="id"
          @deselect="handleProgramDeselect"
        />
      </div>
    </div>
    <div
      v-if="enableTaxonomicGroupFilter"
      class="field"
    >
      <label class="label">Taxonomic Group</label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.taxonomicGroup">
            <option
              :value="null"
              selected
            >
              All
            </option>
            <option
              v-for="group in options.taxonomicGroup"
              :key="group"
              :value="group"
            >
              {{ group }}
            </option>
          </select>
        </div>
      </div>
    </div>
    <div
      v-if="enableTaxonStatusFilter"
      class="field"
    >
      <label class="label">Taxon Status</label>
      <div
        class="control"
        style="margin-bottom: 1em;"
      >
        <div class="select">
          <select v-model="criteria.statusAuthority">
            <option
              :value="null"
              selected
            >
              Select authority…
            </option>
            <option
              v-for="authority in options.statusAuthority"
              :key="authority.id"
              :value="authority"
            >
              {{ authority.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="control">
        <div
          v-for="taxonStatus in options.taxonStatus"
          :key="taxonStatus.id"
        >
          <label><input
            v-model="criteria.taxonStatus"
            type="checkbox"
            :value="taxonStatus"
            :disabled="criteria.statusAuthority == null"
          > {{ taxonStatus.name }}</label>
        </div>
      </div>
    </div>
    <div
      v-if="enableTaxonStatusFilter"
      class="field"
    >
      <label class="label">Taxon Eligibility</label>
      <div
        class="control"
        style="margin-bottom: 1em;"
      >
        <label><input
          v-model="criteria.eligibleForTSXOnly"
          type="checkbox"
        > Only include taxa eligible for inclusion in the TSX</label>
      </div>
    </div>
    <div
      class="field"
      data-test="species-filter"
    >
      <label class="label">Species</label>
      <div class="control">
        <Multiselect
          v-model="criteria.species"
          mode="multiple"
          :options="querySpecies"
          :delay="500"
          :searchable="true"
          :close-on-select="false"
          :filter-results="false"
          no-options-text="No species found"
          placeholder="All species"
          label="label"
          value-prop="id"
          @open="(select) => select.refreshOptions()"
        />
      </div>
      <div style="border-left: 2px solid #eee; padding-left: 1em;">
        <div
          class="buttons"
          style="margin-top: 1em;"
        >
          <button
            class="button is-small is-light"
            @click="importSpeciesList"
          >
            Import List
          </button>
          <button
            v-if="criteria.species.length"
            class="button is-small is-light"
            @click="exportSpeciesList"
          >
            Export List
          </button>
          <tippy
            class="info-icon icon"
            arrow
            interactive
            placement="right"
            style="margin-bottom: 0.5rem;"
          >
            <template #default>
              <i class="far fa-question-circle" />
            </template>
            <template #content>
              <div class="popup-content content has-text-white">
                <p>A list of selected species can be imported from a file in CSV format.</p>
                <p>The file must contain a column named <em>TaxonID</em> listing the taxon ID of each species.</p>
                <p>
                  A full list of taxon IDs can be found in the <a
                    href="https://tsx.org.au/files/TaxonList.xlsx"
                    download
                  >Taxon List</a>.
                </p>
              </div>
            </template>
          </tippy>
        </div>
        <table
          v-if="criteria.species.length"
          style="border: 1px solid #ccc;"
          class="table is-narrow"
        >
          <thead>
            <tr>
              <th>Common name</th>
              <th>Scientific name</th>
              <th>Taxon ID</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="speciesId in criteria.species"
              :key="speciesId"
            >
              <td>{{ speciesById(speciesId).common_name }}</td>
              <td>{{ speciesById(speciesId).scientific_name }}</td>
              <td>{{ speciesId }}</td>
              <td>
                <button
                  class="delete is-small"
                  style="margin-top: 4px"
                  @click="deselectSpecies(speciesId)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      class="field"
      data-test="site-filter"
    >
      <label class="label">Sites</label>
      <div class="control">
        <Multiselect
          v-model="criteria.sites"
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
          v-if="criteria.sites.length"
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
              v-for="(siteInfo, index) in criteria.sites"
              :key="index"
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

    <div
      v-if="enableManagementFilter"
      class="field"
    >
      <label class="label">Management
        <tippy
          class="info-icon icon"
          arrow
          interactive
          placement="right"
          style="margin-bottom: 0.5rem;"
        >
          <template #default><i class="far fa-question-circle" /></template>
          <template #content>
            <div
              class="popup-content content has-text-white"
              style="font-weight: normal;"
            >
              <p>The ‘No known management’ filtering option includes sites that fall into the ‘No management’ and ‘Unknown’ categories from the TSX data import template.</p>
            </div>
          </template>
        </tippy>
      </label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.management">
            <option
              :value="null"
              selected
            >
              All sites (managed & unmanaged)
            </option>
            <option>Actively managed</option>
            <option>No known management</option>
          </select>
        </div>
      </div>
    </div>
  </fieldset>
  <div
    v-if="statsDescription"
    class="notification"
  >
    <p>{{ statsDescription }}</p>
    <p v-if="excludedStatsDescription">
      {{ excludedStatsDescription }}
    </p>
  </div>
  <div
    v-else
    class="notification"
  >
    Loading...
    <spinner
      size="small"
      style="display: inline-block;"
    />
  </div>

  <div
    v-if="enableMap"
    class="block"
    style="width: 100%; max-width: 640px; height: 480px; display: block; background: #eee;"
  >
    <HeatMap
      :heatmap-data="heatmapData"
      :loading="heatmapLoading"
    />
  </div>

  <slot name="downloads-title" />

  <div class="block">
    <button
      type="button"
      class="button is-primary"
      :disabled="!enableDownload"
      @click="downloadRawData"
    >
      Download Raw Data (CSV format)
    </button>
  </div>
  <div class="block">
    <button
      type="button"
      class="button is-primary"
      :disabled="!enableDownload"
      @click="downloadTimeSeries"
    >
      Download Time Series (CSV format)
    </button>
  </div>

  <div class="block">
    <button
      type="button"
      class="button is-primary"
      :disabled="!enableDownload && consistencyPlotStatus != 'processing'"
      @click="generateConsistencyPlot"
    >
      Generate Monitoring Consistency Plot
    </button>
  </div>
  <div v-if="consistencyPlotStatus == 'processing'">
    <spinner size="small" />
  </div>
  <div
    v-if="consistencyPlotStatus == 'ready'"
    class="content"
  >
    <p style="font-style: italic;">
      The below dot plot shows the distribution of surveys at unique sites. Each row represents a time series in the dataset or data subset where a species/subspecies was monitored with a consistent method and unit of measurement at a single site over time. The maximum number of time-series included in this plot is 50.
    </p>
    <canvas
      ref="consistencyPlot"
      style="height: 25em; max-height: 25em;"
    />
    <p>
      <button
        type="button"
        class="button is-primary"
        @click="downloadConsistency"
      >
        Download Monitoring Consistency Plot (CSV format)
      </button>
    </p>
  </div>
  <div
    v-if="consistencyPlotStatus == 'error'"
    class="content"
  >
    <p>An error occurred while generating the monitoring consistency plot.</p>
  </div>

  <hr>

  <div class="block">
    <h4 class="title is-6">
      Population Trend
    </h4>
    <div class="sideborder block">
      <div class="field is-horizontal">
        <div class="field-label is-normal">
          <label class="label">Reference year</label>
        </div>
        <div class="field-body">
          <div class="control">
            <div class="select">
              <select
                v-model="trendReferenceYear"
                :disabled="!enableTrendParams"
              >
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
      <div class="field is-horizontal">
        <div class="field-label is-normal">
          <label class="label">Final year</label>
        </div>
        <div class="field-body">
          <div class="control">
            <div class="select">
              <select
                v-model="trendFinalYear"
                :disabled="!enableTrendParams"
              >
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
      <p
        v-if="trendParamsError"
        class="help is-danger block"
      >
        {{ trendParamsError }}
      </p>
    </div>
  </div>

  <div class="block">
    <button
      type="button"
      class="button is-primary"
      :disabled="!enableGenerateTrend"
      @click="generateTrend"
    >
      Generate Population Trend
    </button>
    <p
      v-if="trendStatus == 'error'"
      class="help is-danger block"
    >
      An error occurred while generating the trend.
    </p>
  </div>

  <div
    v-if="trendStatus == 'processing'"
    class="block"
  >
    Please wait while the population trend is generated. This may take several minutes.
    <spinner
      size="small"
      style="display: inline-block;"
    />
  </div>
  <div
    v-if="trendStatus == 'ready'"
    class="content"
  >
    <p v-if="isAdmin">
      {{ trendDiagnosticsText }}
    </p>
    <p style="font-style: italic;">
      The below trend graph shows the average change in populations compared to a baseline year. It shows a relative change and not population numbers themselves. At the reference year, the index gets an index score of one. A score of 1.2 would mean a 20% increase on average compared to the reference year, while a score of 0.8 would mean a 20% decrease on average compared to the reference year. The overall trend (mean value per year) is shown by the blue line (dashed for single species and solid for multiple species). The grey cloud indicates the uncertainty in the estimate as measured by the variability between all-time series in the dataset or data subset. This trend excludes one-off surveys and absent-only time series. Please note that this trend has been generated using the Living Planet Index methodology, which is designed for producing composite trends rather than single-species trends.
    </p>
    <canvas
      v-show="showPlot"
      ref="plot"
      style="height: 10em;"
    />
    <p>
      <button
        type="button"
        class="button is-primary"
        @click="downloadTrend"
      >
        Download Population Trend (CSV format)
      </button>
    </p>
    <p>
      <button
        type="button"
        class="button is-primary"
        @click="downloadTrendImage"
      >
        Download Population Trend (PNG format)
      </button>
    </p>
  </div>
  <div
    v-if="trendStatus == 'empty'"
    class="block"
  >
    <p>Insufficient data available to generate a trend</p>
  </div>
</template>

<script>
import * as api from '../api.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'
import Multiselect from '@vueform/multiselect'
import HeatMap from './HeatMap.vue'
import { plotTrend, generateTrendPlotData, trendDiagnosticsText } from '../plotTrend.js'
import { plotConsistency } from '../plotConsistency.js'
import { Tippy } from 'vue-tippy'
import { readTextFile, extractSpeciesIDsFromCSV, saveTextFile, generateSpeciesCSV } from '../util.js'
import { markRaw } from 'vue'

export default {
  name: 'CommonDownloads',
  components: {
    Spinner,
    Multiselect,
    Tippy,
    HeatMap
  },
  props: {
    sourceId: {
      type: Number,
      default: null
    },
    enableProgramFilter: Boolean,
    enableStateFilter: Boolean,
    enableManagementFilter: Boolean,
    enableTaxonomicGroupFilter: Boolean,
    enableMap: Boolean,
    enableTaxonStatusFilter: Boolean,
    enableRegionFilter: Boolean
  },
  data() {
    return {
      status: 'loading',
      trendStatus: 'idle',
      trendError: null,
      showPlot: false,
      options: {
        state: [
          'Australian Capital Territory',
          'Queensland',
          'New South Wales',
          'Northern Territory',
          'South Australia',
          'Western Australia',
          'Tasmania',
          'Victoria'
        ],
        taxonStatus: [
          { name: 'Least Concern and Unlisted', id: 'LC' },
          { name: 'Near Threatened', id: 'NT' },
          { name: 'Vulnerable', id: 'VU' },
          { name: 'Endangered', id: 'EN' },
          { name: 'Critically Endangered', id: 'CR' },
          { name: 'Extinct', id: 'EX' }
        ],
        statusAuthority: [
          { name: 'Max', id: 'max' },
          { name: 'EPBC', id: 'epbc' },
          { name: 'Australian IUCN status', id: 'iucn' },
          { name: '2020 Bird Action Plan', id: 'bird_action_plan' }
        ],
        monitoringPrograms: [],
        taxonomicGroup: [],
        species: [],
        regions: []
      },
      sitesLoading: false,
      criteria: {
        state: null,
        monitoringPrograms: [],
        species: [],
        sites: [],
        regions: [],
        management: null,
        taxonomicGroup: null,
        taxonStatus: [],
        statusAuthority: null,
        eligibleForTSXOnly: false

      },
      changeCounter: 0, // Incremented every time criteria are changed
      stats: null,
      heatmapLoading: false,
      heatmapData: [],
      trendReferenceYear: null,
      trendFinalYear: null,
      consistencyPlotStatus: 'idle',
      trendDiagnosticsText: null,
      user: null
    }
  },
  computed: {
    submitting: function() {
      return this.status === 'submitting'
    },
    enableDownload: function() {
      return (!this.enableProgramFilter || this.criteria.monitoringPrograms.length > 0) && this.stats && this.stats.sighting_count > 0
    },
    enableGenerateTrend: function() {
      return this.enableDownload
        && this.trendParamsError === undefined
        && this.trendStatus !== 'processing'
    },
    enableTrendParams: function() {
      return this.trendStatus !== 'processing'
    },
    statsDescription: function() {
      let stats = this.stats
      if(stats) {
        let statsPhrases = [
          this.formatQuantity(stats.sighting_count, 'individual survey count'),
          this.formatQuantity(stats.taxon_count, 'taxon', 'taxa'),
          this.sourceId ? [] : this.formatQuantity(stats.source_count, 'dataset'),
          this.formatQuantity(stats.time_series_count, 'time series', 'time series')
        ].flat()

        return 'Selected data subset contains '
          + statsPhrases.slice(0, -1).join(', ') + ' and ' + statsPhrases.slice(-1)[0]
          + '.'
      } else {
        return undefined
      }
    },
    excludedStatsDescription: function() {
      let stats = this.stats
      if(stats?.excluded_time_series_count > 0) {
        return ' This includes '
          + this.formatQuantity(stats.excluded_time_series_count, 'one-off survey')
          + ' or absent-only time series for '
          + this.formatQuantity(stats.excluded_time_series_taxon_count, 'taxon', 'taxa')
          + ', which will not be included in any trends generated.'
      } else {
        return undefined
      }
    },
    availableYears: function() {
      let min = this.stats?.min_year
      let max = this.stats?.max_year
      if(min && max) {
        let years = new Array(max - min + 1)
        for(let i = 0; i < max - min + 1; i++) {
          years[i] = min + i
        }
        return years
      } else {
        return []
      }
    },
    trendParamsError: function() {
      if(this.stats && this.stats.min_year === this.stats.max_year) {
        return 'Insufficient data available to generate a trend'
      }
      if(this.trendReferenceYear >= this.trendFinalYear) {
        return 'Reference year must be earlier than final year'
      }
      return undefined
    },
    isAdmin: function() {
      return this.user?.is_admin
    },
    canAccessAllPrograms() {
      return this.isAdmin
    }
  },
  watch: {
    criteria: {
      handler() {
        this.changeCounter++
        var c = this.changeCounter

        // Wait for criteria to settle
        setTimeout(() => {
          if(c == this.changeCounter) {
            this.updateStats()
            this.trendStatus = 'idle'
            this.showPlot = false
            this.consistencyPlotStatus = 'idle'
          }
        }, 1500)
      },
      deep: true
    }
  },
  created() {
    let initialisationPromises = []

    api.currentUser().then((user) => {
      this.user = user
    })

    if(this.enableProgramFilter) {
      initialisationPromises.push(
        api.currentUser().then((user) => {
          this.user = user
          if(user.is_admin) {
            return api.monitoringPrograms()
          } else {
            return api.programsManagedBy(user.id)
          }
        }).then((programs) => {
          if(this.user.is_admin) {
            programs = [{ description: '(No program)', id: 'none' }].concat(programs)
          }
          this.options.monitoringPrograms = programs
          if(!this.user.is_admin) {
            // select all programs by default
            this.criteria.monitoringPrograms = programs.filter(p => p.id != 'none')
          }
        })
      )
    }

    if(this.enableRegionFilter) {
      this.regionLookup = {}
      initialisationPromises.push(api.regions().then((regions) => {
        for(let region of regions) {
          region.label = region.name + ' (' + region.state + ')'
        }
        regions.sort((a, b) => a.label.localeCompare(b.label))
        this.options.regions = regions
        this.regionLookup = Object.fromEntries(regions.map(r => [r.id, r]))
      }))
    }

    let speciesPromise
    if(this.sourceId) {
      speciesPromise = api.species({ source_id: this.sourceId })
    } else {
      speciesPromise = api.species({ q: 't1_present' })
    }
    this.speciesLookup = {}

    if(this.enableTaxonomicGroupFilter) {
      initialisationPromises.push(
        api.taxonomicGroups().then(options =>
          this.options.taxonomicGroup = options.map(option => option.description)))
    }

    this.criteria.taxonStatus = [...this.options.taxonStatus]

    initialisationPromises.push(speciesPromise.then((species) => {
      species.forEach((sp) => {
        this.speciesLookup[sp.id] = { ...sp, label: speciesLabel(sp) }
      })
    }))

    Promise.all(initialisationPromises).catch((error) => {
      console.log(error)
      this.status = 'error'
    })

    if(!this.enableProgramFilter) {
      // Note: If program filter is enabled, updateStats() will be called once programs are loaded, and calling it now would
      // result in a useless and expensive request
      this.updateStats()
    }
  },
  methods: {
    speciesById: function(id) {
      return this.speciesLookup[id]
    },
    regionById: function(id) {
      return this.regionLookup[id]
    },
    deselectSpecies: function(id) {
      this.criteria.species = this.criteria.species.filter(x => x !== id)
    },
    deselectSite: function(site) {
      this.criteria.sites = this.criteria.sites.filter(x => x != site)
    },
    deselectRegion: function(id) {
      this.criteria.regions = this.criteria.regions.filter(x => x !== id)
    },
    handleProgramDeselect: function(value, option, select$) {
      // Prevent deselection of last program for non-admin
      if(!this.canAccessAllPrograms && this.criteria.monitoringPrograms.length == 0) {
        this.criteria.monitoringPrograms = [value]
      }
    },
    importSpeciesList: function() {
      readTextFile('text/plain, text/csv', (text) => {
        var ids = extractSpeciesIDsFromCSV(text)
        api.speciesForIDs(ids).then((species) => {
          species.forEach((sp) => {
            this.speciesLookup[sp.id] = { ...sp, label: speciesLabel(sp) }
          })
          this.criteria.species = ids
        })
      })
    },
    exportSpeciesList: function() {
      var species = this.criteria.species.map(id => this.speciesById(id))
      var csv = generateSpeciesCSV(species)
      saveTextFile(csv, 'text/csv', 'species-list.csv')
    },
    downloadRawData: function() {
      var params = this.buildDownloadParams()

      // TODO: indicate download is in progress. We could potentially do this with a cookie
      window.location = api.dataSubsetDownloadURL('raw_data', params)
    },
    downloadTimeSeries: function() {
      var params = this.buildDownloadParams()
      window.location = api.dataSubsetDownloadURL('time_series', params)
    },
    generateTrend: function() {
      let params = {
        reference_year: this.trendReferenceYear,
        final_year: this.trendFinalYear,
        ...this.buildDownloadParams()
      }
      let v = this.changeCounter // used to detect if parameters are changed during trend generation
      this.trendDiagnosticsText = null
      this.trendStatus = 'processing'
      api.dataSubsetGenerateTrend(params).then((x) => {
        this.trendId = x.id
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrendStatus(x.id, v), 3000)
      }).catch((e) => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    checkTrendStatus: function(id, v) {
      if(v != this.changeCounter) {
        return
      }
      api.dataSubsetTrendStatus(id).then((x) => {
        if(x.status == 'ready') {
          this.trendDownloadURL = api.dataSubsetTrendDownloadURL(id)
          this.plotTrend(id, v)
          this.updateTrendDiagnostics(id, v)
        } else if(x.status == 'processing') {
          setTimeout(() => this.checkTrendStatus(id, v), 3000)
        }
      }).catch((e) => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    downloadTrend() {
      window.location = this.trendDownloadURL
    },
    downloadTrendImage() {
      let params = this.buildDownloadParams()

      api.dataSubsetFilenameComponent(params).then((filenameComponent) => {
        let a = document.createElement('a')
        a.download = 'tsx-trend&' + filenameComponent + '.png'
        a.href = this.$refs.plot.toDataURL('image/png')
        a.click()
      })
    },
    plotTrend(id, v) {
      api.dataSubsetTrend(id).then((data) => {
        if(v != this.changeCounter) {
          return
        }

        let plotData = generateTrendPlotData(data)
        let isEmpty = plotData.labels.length < 2

        if(isEmpty) {
          this.trendStatus = 'empty'
        } else {
          this.trendStatus = 'ready'
          setTimeout(() => {
            this.showPlot = true
            plotTrend(data, this.$refs.plot)
          })
        }
      }).catch((e) => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    updateTrendDiagnostics(id, v) {
      api.dataSubsetTrendDiagnostics(id).then((data) => {
        if(v != this.changeCounter) {
          return
        }

        this.trendDiagnosticsText = trendDiagnosticsText(data)
      })
    },
    generateConsistencyPlot() {
      let params = this.buildDownloadParams()
      this.consistencyPlotStatus = 'processing'
      let v = this.changeCounter
      api.dataSubsetConsistencyPlot(params).then((data) => {
        if(v != this.changeCounter) {
          return
        }
        this.consistencyPlotStatus = 'ready'
        this.consistencyPlotData = data
        setTimeout(() => {
          plotConsistency(data, this.$refs.consistencyPlot)
        })
      }).catch((e) => {
        if(v != this.changeCounter) {
          return
        }
        console.log(e)
        this.consistencyPlotStatus = 'error'
      })
    },
    downloadConsistency() {
      var params = this.buildDownloadParams()

      window.location = api.dataSubsetDownloadURL('monitoring_consistency_all', params)
    },
    buildDownloadParams: function() {
      var params = {}

      if(this.sourceId) {
        params.source_id = this.sourceId
      }

      if(this.enableProgramFilter && this.criteria.monitoringPrograms.length > 0) {
        params.monitoring_programs = this.criteria.monitoringPrograms
      }

      if(this.enableRegionFilter && this.criteria.regions.length > 0) {
        params.regions = this.criteria.regions.join(',')
      }

      if(this.enableStateFilter && this.criteria.state) {
        params.state = this.criteria.state
      }

      if(this.enableManagementFilter && this.criteria.management) {
        params.management = this.criteria.management
      }

      if(this.criteria.species && this.criteria.species.length > 0) {
        params.taxon_id = this.criteria.species.join(',')
      }

      if(this.criteria.sites && this.criteria.sites.length > 0) {
        params.site_id = this.criteria.sites.map(x => x.split(',')[0]).join(',')
      }

      if(this.enableTaxonomicGroupFilter && this.criteria.taxonomicGroup) {
        params.taxonomic_group = this.criteria.taxonomicGroup
      }

      if(this.enableTaxonStatusFilter && this.criteria.statusAuthority) {
        params.status_auth = this.criteria.statusAuthority.id
        params.taxon_status = this.criteria.taxonStatus.map(x => x.id).join(',')
      }

      if(this.enableTaxonStatusFilter && this.criteria.eligibleForTSXOnly) {
        params.eligible_for_tsx_only = 'true'
      }

      return params
    },
    formatQuantity: function(x, singular, plural) {
      plural = plural || singular + 's'
      if(x == 0) {
        return 'no ' + plural
      } else if(x == 1) {
        return x + ' ' + singular
      } else {
        return x.toLocaleString() + ' ' + plural
      }
    },
    querySites: function(query) {
      let params = this.buildDownloadParams()
      delete params.site_id
      params.site_name_query = query || ''
      return api.dataSubsetSites(params)
        .then(sites => sites.map(site => ({ name: site.name, id: site.id + ',' + site.name })))
    },
    querySpecies: function(query) {
      let params = this.buildDownloadParams()
      delete params.taxon_id
      params.species_name_query = query || ''
      return api.dataSubsetSpecies(params)
        .then(species => species.map(sp => ({ ...sp, label: speciesLabel(sp) })))
    },
    queryRegions: async function(query) {
      return this.options.regions.filter(region =>
        !this.criteria.state || region.state == this.criteria.state)
    },
    updateStats: function() {
      this.stats = null
      var params = this.buildDownloadParams()
      let v = this.changeCounter
      api.dataSubsetStats(params).then((stats) => {
        if(v === this.changeCounter) {
          this.stats = stats
          this.trendReferenceYear = this.stats.min_year
          this.trendFinalYear = this.stats.max_year
        }
      })
      if(this.enableMap) {
        this.heatmapLoading = true
        api.dataSubsetIntensityMap(params).then((data) => {
          if(v === this.changeCounter) {
            this.heatmapData = markRaw(data)
          }
        }).finally(() => {
          if(v === this.changeCounter) {
            this.heatmapLoading = false
          }
        })
      }
    }
  }
}

function speciesLabel(sp) {
  return sp.scientific_name + ' (' + (sp.common_name ? (sp.common_name + ', ') : '') + sp.id + ')'
}
</script>

<style>
.multiselect-search { height: 100%; } /* Fixes alignment issue with multiselect component */
.popup-content a { color: #aaa; text-decoration: underline; }
.popup-content a:hover { color: #ccc; }
.sideborder {
  border-left: 2px solid #eee;
  padding-left:  1em;
}
</style>
<style src="@vueform/multiselect/themes/default.css"></style>

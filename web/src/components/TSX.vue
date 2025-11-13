<template>
  <div
    class="section is-dark"
    style="padding-bottom: 1em;"
  >
    <div class="container is-widescreen">
      <div class="content">
        <div class="tile is-ancestor">
          <div class="tile is-2 is-parent">
            <div class="tile is-child">
              <div class="field">
                <GenericField
                  v-if="queryTypeField"
                  v-model:value="fieldValues.type"
                  :field="queryTypeField"
                />
              </div>
              <hr>
              <div
                class="content"
                style="display: flex; justify-content: space-between; margin-bottom: 0;"
              >
                <h4 class="is-title has-text-white">
                  Filters
                </h4>
                <button
                  class="button is-primary is-small"
                  style="position: relative; top: -0.3em;"
                  @click="reset"
                >
                  Reset
                </button>
              </div>
              <p class="content is-size-7">
                Only selections with adequate data are shown.
              </p>

              <div style="margin-bottom: 1em">
                <template
                  v-for="field in sidebarFields"
                  :key="field.name"
                >
                  <GenericField
                    v-if="!field.disabled"
                    v-model:value="fieldValues[field.name]"
                    :field="field"
                    style="margin-bottom: 0.8em;"
                  />
                </template>
              </div>

              <p
                v-if="fieldValues && fieldValues.type == 'individual'"
                class="content is-size-7"
              >
                NOTE: The LPI method was not designed for single-species trends. These trends vary greatly in reliability, with some having very sparse underlying data.
              </p>
              <hr>

              <div v-if="!noData">
                <div class="dropdown is-hoverable">
                  <div class="dropdown-trigger">
                    <button
                      class="button is-primary"
                      aria-haspopup="true"
                      area-controls="dropdown-menu"
                    >
                      <span>Download</span>
                      <span class="icon is-small">
                        <i
                          class="fas fa-angle-down"
                          aria-hidden="true"
                        />
                      </span>
                    </button>
                  </div>
                  <div class="dropdown-menu">
                    <div class="dropdown-content">
                      <div
                        class="dropdown-item is-clickable hover-highlight"
                        @click="downloadCSV"
                      >
                        Time series (CSV)
                      </div>
                      <div
                        class="dropdown-item is-clickable hover-highlight"
                        @click="downloadTrend"
                      >
                        Trend (CSV)
                      </div>
                      <div
                        class="dropdown-item is-clickable hover-highlight"
                        @click="viewDataSummary"
                      >
                        Data summary
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-show="loadingData && !showFullMap"
            class="modal is-active"
          >
            <div
              class="modal-background"
              style="background: rgba(0,0,0,0.2)"
            />
            <div class="modal-card">
              <section class="modal-card-body">
                <spinner
                  size="large"
                  message="Loading data...."
                />
              </section>
            </div>
          </div>

          <div
            v-show="!noData"
            class="tile is-vertical"
          >
            <div class="tile is-block-tablet is-flex-widescreen">
              <div
                v-show="!showFullMap"
                class="tile is-parent is-vertical"
              >
                <div class="tile is-child card">
                  <div
                    style="
                display: flex;
                flex-wrap: nowrap;
                gap: 1em;
                justify-content: space-between;
                margin-right: 2.5em;
                align-items: center;
                margin-bottom: 0.8em;
                "
                  >
                    <h4
                      class="has-text-black"
                      style="
                  white-space:nowrap;
                  margin-bottom: 0;
                  "
                    >
                      Main index
                    </h4>
                    <div
                      v-if="referenceYearField"
                      style="
                  display: flex;
                  flex-wrap: nowrap;
                  gap: 0.5em;
                  align-items: center;"
                    >
                      <div
                        class="is-content refyear-label"
                        style="font-size: 0.8rem"
                      >
                        Reference year
                      </div>
                      <GenericField
                        v-model:value="fieldValues.refyear"
                        :field="referenceYearField"
                      />
                    </div>
                  </div>
                  <tippy
                    class="info-icon icon"
                    arrow
                    interactive
                    placement="left"
                  >
                    <template #default>
                      <i class="far fa-question-circle" />
                    </template>
                    <template #content>
                      <div class="popup-content">
                        <p>The index shows the average change in populations compared to a base year. It shows a relative change and not population numbers themselves. At the reference year, the index gets an index score of one. A score of 1.2 would mean a 20% increase on average compared to the reference year, while a score of 0.8 would mean a 20% decrease on average compared to the reference year.</p>
                        <p>Check this index:</p>
                        <ol>
                          <li>Look at <b>Spatial representativeness</b> map to see how much data there are and where these data come from.</li>
                          <li>Look at <b>Monitoring consistency</b> to see how consistently each monitoring location was visited over time.</li>
                          <li>Go to <b>Time series and species accumulation</b> plot to see how many time series and species/subspecies were used to calculate this index in each year</li>
                          <li>Adjust the <b>Reference year</b> to let the index start at a year with more data</li>
                          <li>Go to <b>Data Summary</b> to see which species/subspecies were included in this index</li>
                          <li>Go to <b>Download CSV</b> to get the aggregated data used to calculate this index.</li>
                        </ol>
                        <p>
                          The three-year lag in the index is implemented due to a downturn in data availability closer to the release year of the index. To read more about this, please see the pop-up info box for the ‘Number of time series and species per year’ plot in the bottom right of this tool.
                        </p>
                      </div>
                    </template>
                  </tippy>
                  <div
                    v-show="!noLPI"
                    class="plot-container"
                  >
                    <canvas ref="lpiplot" />
                  </div>
                  <div
                    v-show="noLPI"
                    class="has-text-black"
                  >
                    <p>No index available – less than 3 taxa present at all possible reference years.</p>
                  </div>
                </div>
                <div class="tile is-child card">
                  <h4 class="has-text-black">
                    Monitoring consistency
                  </h4>
                  <tippy
                    class="info-icon icon"
                    arrow
                    interactive
                    placement="left"
                  >
                    <template #default>
                      <i class="far fa-question-circle" />
                    </template>
                    <template #content>
                      <div class="popup-content">
                        This dot plot shows the particular years for which monitoring data were available, from a random 50 site sample of the whole dataset (or data subset). Each row represents a time series where a species/subspecies was monitored with a consistent method at a single site. The dots represent count values for the metric used to quantify the species/subspecies while zeros indicate absences (non-detections) of those species at the site.
                      </div>
                    </template>
                  </tippy>
                  <div class="plot-container">
                    <canvas ref="dotplot" />
                  </div>
                </div>
              </div>
              <div class="tile is-parent is-vertical">
                <div class="tile is-child card map-tile">
                  <h4 class="has-text-black">
                    Spatial representativeness
                  </h4>
                  <tippy
                    class="info-icon icon"
                    arrow
                    interactive
                    placement="left"
                  >
                    <template #default>
                      <i class="far fa-question-circle" />
                    </template>
                    <template #content>
                      <div class="popup-content">
                        The spatial representativeness map shows where the monitoring data used to calculate a particular index was recorded in Australia. Sites are buffered to obscure precise locations.
                      </div>
                    </template>
                  </tippy>
                  <div
                    id="intensityplot"
                    ref="intensityplot"
                    class="heatmap-div"
                  />
                  <spinner
                    v-show="loadingMap"
                    size="medium"
                    class="heatmap-spinner"
                  />
                </div>
                <div
                  v-show="!showFullMap"
                  class="tile is-child card"
                >
                  <h4 class="has-text-black">
                    Number of time series and species per year
                  </h4>
                  <tippy
                    class="info-icon icon"
                    arrow
                    interactive
                    placement="left"
                  >
                    <template #default>
                      <i class="far fa-question-circle" />
                    </template>
                    <template #content>
                      <div class="popup-content">
                        This plot shows the number of species/subspecies (in blue) and the number of time series (in green) available in each year to calculate the index. The number of species and time series will always decline closer to the final year, given the lag in integration of datasets into the index (resulting primarily from the lag in the availability of data, given that it takes time for data providers to collate and submit, or takes time for the TSX team to identify data in the literature). This downturn in data availability closer to the release year is the reason that a 3-year lag is implemented in trend calculation, as data quality is poorer closer to the release year.
                      </div>
                    </template>
                  </tippy>
                  <div class="plot-container">
                    <canvas ref="sumplot" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-show="noData"
            class="tile is-child"
          >
            <p style="margin: 0.8em">
              {{ noDataMessage() }}
            </p>
          </div>
        </div>

        <div class="content">
          <a
            class="has-text-white"
            style="text-decoration: underline;"
            href="https://tsx.org.au/terms-of-use/"
            target="_blank"
          >Terms of Use</a>
        </div>

        <!-- warning dialog -->
        <div
          v-show="!hasAcceptedWarning"
          class="modal is-active"
        >
          <div class="modal-background" />
          <div class="modal-card">
            <header class="modal-card-head">
              <span class="modal-card-title">Caution</span>
            </header>
            <section
              class="modal-card-body"
              style="color:black"
            >
              <p>The trends produced by this tool vary in their reliability. While the TSX team implements rigorous data quality standards, a trend is ultimately only as good as the underlying data.</p>
              <p>We have developed diagnostic tools to help assess the reliability of each trend.</p>
              <p>
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://tsx.org.au/visualising-the-index/how-good/"
                >(Click here for more details on how to assess reliability of trends)</a>
              </p>
              <p>Please also note that the trends for reptiles are a pilot index, with further data to be added in 2026. The trends shown should be considered interim.</p>
              <p>By using this tool, you acknowledge the precautions regarding trend generation and reliability.</p>
            </section>
            <footer class="modal-card-foot">
              <button
                class="button"
                @click="acceptWarning"
              >
                I Accept
              </button>
              <button
                class="button"
                @click="goBack"
              >
                Cancel
              </button>
            </footer>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import * as api from '../api.js'
import {
  Chart,
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
} from 'chart.js'

Chart.register(
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
)

import Spinner from 'vue-simple-spinner/src/components/Spinner.vue'
import L from 'leaflet'
import HeatmapOverlay from 'heatmap.js/plugins/leaflet-heatmap/leaflet-heatmap.js'
import 'leaflet-easybutton/src/easy-button.js'
import { min, max, pluck, uniq, parseParams, encodeParams, deepEquals, saveTextFile } from '../util.js'
import { Tippy } from 'vue-tippy'
import GenericField from './GenericField.vue'
import { generateTrendPlotData, plotTrend } from '../plotTrend.js'

const dataset = 'test'
const enableIndividualTrends = false

export default {
  name: 'TSX',
  components: {
    Spinner,
    Tippy,
    GenericField
  },
  data () {
    var data = {
      fields: [], // Field definitions from server
      fieldValues: null, // Curent field values, bound to inputs
      dataParams: null,
      // is loading data
      loadingData: false,
      // no data to show
      noData: true,
      // no LPI run to show
      noLPI: false,
      // prioritySelected
      prioritySelected: false,
      // heatmap
      // intensity plot
      loadingMap: false,
      // heatmapLayer: null,
      trendData: null,

      // map: null,
      showFullMap: false,
      hasAcceptedWarning: localStorage.getItem('hasAcceptedWarning') || false
    }

    return data
  },
  computed: {
    sidebarFields() {
      return this.fields.filter(f => f.name != 'refyear' && f.name != 'type')
    },
    queryTypeField() {
      return this.fields.find(f => f.name == 'type')
    },
    referenceYearField() {
      return this.fields.find(f => f.name == 'refyear')
    },
    filterQueryString() {
      var params = this.latestFieldValuesFromServer()
      delete params.dataset
      return Object.entries(params).map(x => x[0] + '=' + encodeURIComponent(x[1])).join("&")
    },
    filterFilenamePart() {
      var name = decodeURIComponent(this.filterQueryString).replace(/[<>:"/\\|?*]/g, '-')
      if(dataset) {
        name = "dataset=" + dataset + "&" + name
      }
      return name
    },
    downloadTrendURL() {
      return api.trendURL(this.dataParams)
    }
  },
  watch: {
    fieldValues: {
      handler(val, oldVal) {
        if(oldVal == null || !deepEquals(val, this.latestFieldValuesFromServer())) {
          this.updateFields()
        }
      },
      deep: true
    },
    filterQueryString(val) {
      var url = window.location.pathname
      if(val) {
        url += '?' + val
      }
      history.replaceState(null, '', url)
    }
  },
  created () {
  },
  mounted () {
    Chart.defaults.font.size = 14
    this.createMonitoringConsistencyPlot()
    this.createMainIndexPlot()

    // -------intensity plot ----------------
    var baseLayer = L.tileLayer(
      '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    this.heatmapLayer = new HeatmapOverlay({
      'fullscreenControl': true,
      'radius': 0.45,
      'maxOpacity': 0.8,
      'minOpacity': 0.5,
      'blur': 0.75,
      'scaleRadius': true,
      'useLocalExtrema': false,
      latField: 'lat',
      lngField: 'long',
      valueField: 'count',
      gradient: {0.25: 'rgb(0,94,255)', 0.5: 'rgb(0,0,255)', 0.85: 'rgb(163,0,255)', 1.0: 'rgb(255,0,255)'}
    })
    this.map = new L.Map('intensityplot', {
      center: new L.LatLng(-25.917574, 132.702789),
      zoom: 3,
      layers: [baseLayer, this.heatmapLayer]
    })
    // /////////// map control /////////////////////////

    L.easyButton({
      id: 'expand',
      position: 'bottomleft',
      states: [{
        icon: '<strong style="color: black">&swarr;</strong>',
        stateName: 'small',
        onClick: (btn, map) => {
          btn.state('big')
          this.showFullMap = true
          setTimeout(function() { window.dispatchEvent(new Event('resize')) })
        }
      }, {
        icon: '<strong style="color: black">&nearr;</strong>',
        stateName: 'big',
        onClick: (btn, map) => {
          btn.state('small')
          this.showFullMap = false
          setTimeout(function() { window.dispatchEvent(new Event('resize')) })
        }
      }]
    }).addTo(this.map)
    //
    // this is a hack so that leaflet displays properlly
    setTimeout(() => {
      this.map.invalidateSize()
    }, 2000)

    this.updateFromQueryString()
  },
  methods: {
    reset() {
      this.fieldValues = { type: this.fieldValues.type }
    },
    noDataMessage() {
      if(this.fieldValues && this.fieldValues.type == 'individual') {
        return "";
      } else {
        return "(No data to show)"
      }
    },
    updateFields() {
      let params

      // Special logic to reset fields when type changes
      let lastType = this.latestFieldValuesFromServer().type
      if(lastType && lastType != this.fieldValues.type) {
        params = { type: this.fieldValues.type }
      } else {
        params = this.fieldValues
      }

      params = {
        dataset: dataset,
        ...params
      }

      this.loadingData = true
      api.visualisationParameters(params).then(result => {
        let typeField = result.fields.find(x=>x.name=='type')

        if(!enableIndividualTrends) {
          // Hide individual trends
          typeField.options = typeField.options.filter(x => x.value != 'individual')
        }

        let priorityOption = typeField.options.find(x => x.value == 'priority')

        if(priorityOption) {
          priorityOption.help = `<p>
            The Australian Government’s Threatened Species Action Plan 2022–2032 identifies 110 Priority Species that require focussed conservation action. <a style="color: white; text-decoration: underline;" href="https://www.dcceew.gov.au/environment/biodiversity/threatened/publications/priority-species" target="_blank">Learn more.</a>
            </p>`
        }

        this.fields = result.fields
        this.fieldValues = this.latestFieldValuesFromServer()
        this.dataParams = result.data_params
        this.updateMapAndPlots(this.dataParams)
      })
    },
    latestFieldValuesFromServer() {
      return Object.fromEntries(
        this.fields.map(field => [field.name, field.value]))
    },
    isDisabled(field) {
      return false
    },
    updateFromQueryString() {
      var params = parseParams(window.location.search.substr(1))
      delete params.dataset
      this.fieldValues = params
    },
    updateManagementList() {
      if(this.managementEnabled) {
        this.managementList = managementTypes
      } else {
        this.managementList = []
      }
    },
    createMainIndexPlot() {
      this.mainIndexPlot = plotTrend("", this.$refs.lpiplot)
      this.mainIndexPlot.options.scales.yAxis.title.display = false
      this.mainIndexPlot.options.scales.xAxis.title.display = false
      this.mainIndexPlot.options.maintainAspectRatio = false
    },
    updateMainIndexPlot(params) {
      let plotData = this.mainIndexPlot.data
      plotData.labels = []
      plotData.datasets.forEach(x => x.data = [])

      this.trendData = null

      var token = this.updateMainIndexPlot.token = {}
      var stale = () => this.updateMainIndexPlot.token != token

      return api.trend({ format: 'raw', ...params }).then((data) => {
        if(stale()) {
          return
        }
        if(data) {
          this.trendData = data
          let plotOptions = { ignoreNumSpecies: true }

          Object.assign(plotData, generateTrendPlotData(data, plotOptions))
          let minYear = plotData.labels[0]
          this.mainIndexPlot.options.scales.yAxis.title.text = 'Index (' + minYear + ' = 1)'

          // update lpi plot
          this.noLPI = false
          this.mainIndexPlot.update()
        } else {
          this.noLPI = true
        }
      }).catch((e) => {
        if(!stale()) {
          console.log(e)
          this.noLPI = true
        }
      })
    },
    createMonitoringConsistencyPlot() {
      let data = {
        datasets: [{
          label: 'count > 0',
          backgroundColor: '#333',
          borderColor: '#333',
          borderWidth: 1,
          data: [] },
        {
          label: 'count = 0',
          backgroundColor: '#ccc',
          borderColor: '#ccc',
          borderWidth: 1,
          data: [] }]
      }
      this.monitoringConsistencyPlot = new Chart(this.$refs.dotplot.getContext('2d'), {
        type: 'bubble',
        data: data,
        options: {
          animation: false,
          responsive: true,
          maintainAspectRatio: false,
          tooltips: {
            mode: 'point'
          },
          plugins: {
            tooltip: {
              callbacks: {
                label(context) {
                  return context.label + ' (' + context.parsed.x + ')'
                }
              }
            }
          },
          scales: {
            yAxis: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Sites (time series)'
              },
              ticks: {
                callback: function(label, index, labels) {
                  return Number.isInteger(label) ? label.toString() : ''
                }
              }
            },
            xAxis: {
              type: 'linear',
              ticks: {
                callback: function(label, index, labels) {
                  return Number.isInteger(label) ? label.toString() : ''
                }
              }
            }
          }
        }
      })
    },
    updateMonitoringConsistencyAndSummaryPlot(params) {
      return api.diagnosticPlots(params).then((data) => {
          this.noData = data.dotplot.length === 0
          this.refreshMonitoringConsistencyPlot(data.dotplot)
          this.refreshSummaryPlot(data.summary)
        })
    },
    updatePlots(params) {
      this.loadingData = true
      Promise.all([
        this.updateMainIndexPlot(params),
        this.updateMonitoringConsistencyAndSummaryPlot(params),
      ]).finally(x => {
        this.loadingData = false
      })
    },
    updateMap(params) {
      // intensity plot
      this.loadingMap = true

      api.spatialIntensity(params).then((data) => {
        let surveyData = data.map(function(timeSeries) {
          return {
            lat: timeSeries[1],
            long: timeSeries[0],
            count: timeSeries[2]
          }
        })

        let counts = pluck(surveyData, 'value')

        // A scaling factor (/20) is chosen for aesthetic reasons.
        // Previously we were stacking points from many years on top of each other on the map, but
        // for performance reasons I have now combined all years into a single point (see 'fast_mode' in lpi_data.py).
        // This resulted in the heatmap being very faint compared to before, this scaling factor increases the intensity.
        this.heatmapLayer.setData({
          min: min(counts),
          max: max(counts) / 20,
          data: surveyData
        })

        let coordinates = data.map(([lng,lat,count]) => L.latLng(lat, lng))

        if(coordinates.length > 0) {
          let bounds = L.latLngBounds(coordinates)

          let australia = [[-43.6, 113.3], [-10.7, 153.6]]
          if(bounds.contains(australia)) {
            bounds = australia
          }

          setTimeout(() => {
            this.map.invalidateSize()
            this.map.fitBounds(bounds, { padding: L.point(10, 10) })
            setTimeout(() => {
              this.map.invalidateSize()
              this.map.fitBounds(bounds, { padding: L.point(10, 10) })
            }, 400)
          }, 400)
        }
      }).finally(() => {
        this.loadingMap = false
      })
    },
    updateMapAndPlots(params) {
      this.updatePlots(params)
      this.updateMap(params)
    },
    downloadCSV: function() {
      let params = {
        format: 'zip',
        download: 'tsxdata.zip',
        data_filename: "tsx-aggregated-data-" + this.filterFilenamePart + ".csv",
        ...this.dataParams
      }
      var url = api.timeSeriesURL(params)
      window.open(url)
    },
    downloadTrend: function(evt) {
      api.trend({ format: 'csv', ...this.dataParams}).then((data) => {
        saveTextFile(data, 'text/csv', "tsx-trend-" + this.filterFilenamePart + ".csv")
      })

      if(evt.shiftKey) {
        this.downloadPlotData()
      }
    },
    downloadPlotData: function() {
      function quote(v) {
        if(typeof v === "string" && v.match(/["\n\r]/)) {
          return JSON.stringify(v)
        } else {
          return v
        }
      }

      function csv(rows) {
        return rows.map(row => row.map(quote).join(',')).join('\n')
      }

      function download(text, filename) {
        var dl = document.createElement("a")
        dl.href="data:text/plain,"+encodeURIComponent(text)
        dl.setAttribute("download", filename)
        dl.click()
      }

      async function save(name, params) {
        var json = await api.diagnosticPlots(params)

        var rows = json.dotplot.flatMap((a, i) => [a.map(b => [i, b[0], b[1]])]).flat()
        rows = [["TimeSeries", "Year", "NonZeroCount"]].concat(rows)

        download(csv(rows), "tsx-dotplot-" + name + ".csv")

        download(csv([["Year", "NumberOfTimeSeries"]].concat(Object.entries(json.summary.timeseries))), "tsx-time-series-" + name + ".csv")
        download(csv([["Year", "NumberOfTaxa"]].concat(Object.entries(json.summary.taxa))), "tsx-taxa-" + name + ".csv")

        // data = await fetch("https://tsx.org.au/tsxapi/lpi-data/intensity?" + params)
        // json = await data.json()
        // download(csv([["Lat", "Lon", "NumberOfSurveys"]].concat(json.map(x => [x[0], x[1], x[2][0][1]]))), prefix + "-intensity.csv")
      }

      save(this.filterFilenamePart, this.dataParams)
    },
    viewDataSummary: function() {
      var url = api.summaryURL(this.dataParams)
      window.open(url)
    },
    acceptWarning: function() {
      localStorage.setItem('hasAcceptedWarning', true)
      this.hasAcceptedWarning = true
    },
    goBack: function() {
      window.history.back()
    },
    refreshMonitoringConsistencyPlot(data) {
     let datasets = this.monitoringConsistencyPlot.data.datasets

      datasets.forEach((dataset, datasetIndex) => {
        dataset.data = data.flatMap((timeSeries, timeSeriesIndex) =>
          timeSeries.filter(([year, count]) => count === 1 - datasetIndex)
            .map(([year, count]) => ({
              x: year,
              y: timeSeriesIndex + 1,
              r: 1
            }))
        )
      })

      this.monitoringConsistencyPlot.update()
    },
    refreshSummaryPlot: function(data) {
      if (this.summaryPlot) {
        this.summaryPlot.destroy()
      }

      let chart = {
        type: 'scatter',
        data: { datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          hoverMode: 'nearest',
          intersect: true,
          plugins: {
            tooltip: {
              callbacks: {
                label(context) {
                  return '(' + context.parsed.x + ', ' + context.parsed.y + ')'
                }
              }
            }
          },
          scales: {
            year: {
              position: 'bottom',
              ticks: {
                callback: function(label, index, labels) {
                  return Number.isInteger(label) ? label.toString() : ''
                }
              }
            }
          }
        }
      }

      if(data.taxa) {
        chart.data.datasets.push({
          label: 'Number of taxa',
          xAxisID: 'year',
          yAxisID: 'numTaxa',
          borderColor: '#58899e',
          backgroundColor: '#58899e',
          data: Object.entries(data.taxa).map(([year, value]) => ({ x: +year, y: +value }))
        })

        chart.options.scales.numTaxa = {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Number of taxa'
          },
          ticks: {
            callback: function(label, index, labels) {
              return Number.isInteger(label) ? label.toLocaleString() : ''
            }
          }
        }
      }

      if(data.timeseries) {
        chart.data.datasets.push({
          label: 'Number of time series',
          xAxisID: 'year',
          yAxisID: 'numTimeSeries',
          borderColor: '#a3c489',
          backgroundColor: '#a3c489',
          data: Object.entries(data.timeseries).map(([year, value]) => ({ x: +year, y: +value }))
        })

        chart.options.scales.numTimeSeries = {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Number of time series'
          },
          grid: {
            display: !data.taxa
          },
          ticks: {
            callback: function(label, index, labels) {
              return Number.isInteger(label) ? label.toLocaleString() : ''
            }
          }
        }
      }

      this.summaryPlot = new Chart(this.$refs.sumplot.getContext('2d'), chart)
    }
  }
}
</script>

<style>
  /*.field-named-state {
    margin-top: 1em;
    border-top: 1px solid white;
    padding-top: 1em;
  }*/
</style>
<style src='leaflet/dist/leaflet.css'>
</style>
<style src='leaflet-easybutton/src/easy-button.css'>
</style>
<style scoped>
  .label {
    color: #fff;
  }
  h4 {
    /*margin-top: 0.5em;*/
    /*margin-left: 1em;*/
  }
  .heatmap-div {
    width: 100%;
    height: 25.5em;
    z-index:1;
  }
  .heatmap-spinner{
    z-index:2;
    position:absolute;
    top: 0.6em;
    right: 4em;
  }
  /* Important: the following line fixes the charts not resizing responsively */
  .tile {
    min-width: 0;
  }
  .tile.card {
    flex-basis: 22.5em;
    max-height: 22.5em;
    height: 22.5em;
    padding: 1em;
  }
  .plot-container {
    position: relative;
    height: 18em;
  }
  .tile.card.map-tile {
    padding: 0;
    padding-top: 1em;
  }
  .tile.card.map-tile h4 {
    margin-left: 1em;
  }

  .card .info-icon {
    color: #aaa;
    position: absolute;
    top: 0.7em;
    right: 1em;
    font-size: 120%;
  }
  .popup-content {
    max-width: 30em;
    text-align: left;
  }
  .popup-content p {
    margin-bottom: 1em;
  }
  .popup-content ol {
    padding-left: 1em;
  }
  .popup-content li {
    margin-bottom: 0.5em;
  }
  .hover-highlight:hover {
    background: #eee;
  }
  hr {
    height: 0px;
  }
  @media screen and (max-width: 500px) {
    .refyear-label {
      display: none;
    }
  }
</style>

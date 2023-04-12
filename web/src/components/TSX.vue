<template>
  <div class="section is-dark" style="padding-bottom: 1em;">
    <div class="container is-widescreen">

  <div class='plot content'>
    <div class="tile is-ancestor">
      <div class="tile is-2 is-parent">
        <div class="tile is-child">
          <div style="margin-bottom: 2em">
            <div class="field" v-for="field in sidebarFields">
              <Field v-if="!field.disabled" :field="field" v-model:value="fieldValues[field.name]"></Field>
            </div>
          </div>
<!--           <p>
            <button class='button is-primary is-small' @click='reset'>Reset</button>
          </p> -->
          <p>
            <button class='button is-primary is-small' @click='downloadCSV'>Download CSV</button>
          </p>
          <p>
            <button class='button is-primary is-small' @click='downloadTrend' :disabled='trendData == null'>Download Trend</button>
          </p>
          <p>
            <button class='button is-primary is-small' @click='viewDataSummary'>Data Summary</button>
          </p>
        </div>
      </div>

      <div class="modal is-active" v-show='loadingData && !showFullMap'>
        <div class="modal-background" style="background: rgba(0,0,0,0.2)"></div>
        <div class="modal-card">
          <section class="modal-card-body">
            <spinner size='large' message='Loading data....'></spinner>
          </section>
        </div>
      </div>

      <div class="tile is-vertical ie11-bugfix" v-show="!noData">
        <div class="tile">
          <div class="tile is-parent is-vertical" v-show="!showFullMap">
            <div class="tile is-child card">
              <div style="display: flex; flex-wrap: nowrap; gap: 1em;">
                <h4 class="has-text-black">Main index</h4>
                <Field :field="referenceYearField" v-if="fieldValues" v-model:value="fieldValues.refyear" style="position: relative; top: -0.5em;"></Field>
              </div>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
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
                  </div>
                </template>
              </tippy>
              <div class="plot-container" v-show="!noLPI">
                <canvas ref='lpiplot'></canvas>
              </div>
              <div class="has-text-black" v-show="noLPI">
                <p>No index available – less than 3 taxa present at all possible reference years.</p>
              </div>
            </div>
            <div class="tile is-child card">
              <h4 class="has-text-black">Monitoring consistency</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This dot plot shows the particular years for which monitoring data were available. Each row represents a time series where a species/subspecies was monitored with a consistent method at a single site. The dots represent count values for the metric used to quantify the species/subspecies while zeros indicate absences (non-detections) of those species at the site.
                  </div>
                </template>
              </tippy>
              <div class="plot-container">
                <canvas ref='dotplot'></canvas>
              </div>
            </div>
          </div>
          <div class="tile is-parent is-vertical">
            <div class="tile is-child card map-tile">
              <h4 class="has-text-black">Spatial representativeness</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This map shows where threatened species data to calculate this index are recorded in Australia. Light blue indicates less data (fewer sites monitored), pink indicates more data (more sites monitored).
                  </div>
                </template>
              </tippy>
              <div id='intensityplot' ref='intensityplot' class='heatmap-div'></div>
              <spinner size='medium' v-show='loadingMap' class='heatmap-spinner'></spinner>
            </div>
            <div class="tile is-child card" v-show="!showFullMap">
              <h4 class="has-text-black">Number of time series and species per year</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This plot shows the number of species/subspecies (in blue) and the number of time series (in green) available in each year to calculate the index.
                  </div>
                </template>
              </tippy>
              <div class="plot-container">
                <canvas ref='sumplot'></canvas>
              </div>
            </div>

          </div>
        </div>
      </div>

      <div class="tile is-child" v-show="noData">
        <p style="margin: 0.8em">{{noDataMessage()}}</p>
      </div>
    </div>

    <!-- warning dialog -->
    <div class="modal is-active" v-show="!hasAcceptedWarning">
      <div class="modal-background"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <span class="modal-card-title">Caution</span>
        </header>
        <section class="modal-card-body" style="color:black">
          <p>This page presents preliminary trends for the 2022 compilation of the Threatened Species Index, for consultation purposes. These trends may change following review by key stakeholders, which will be finalised in early 2023.</p>
          <p>Please also consider that the trends produced by this tool vary in their reliability. While the TSX team implements rigorous data quality standards, a trend is ultimately only as good as the underlying data.</p>
          <p>We have developed diagnostic tools to help assess the reliability of each trend. <a target="_blank" rel="noopener noreferrer" href="https://tsx.org.au/visualising-the-index/how-good/">(Click here for more details on how to assess reliability of trends)</a></p>
          <p>By using this tool you acknowledge the preliminary nature of these trends and the precautions regarding trend generation and reliability.</p>
        </section>
        <footer class="modal-card-foot">
          <button class="button" v-on:click='acceptWarning'>I Accept</button>
          <button class="button" v-on:click='goBack'>Cancel</button>
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
import Field from './Field.vue'

const dataset = 'test'

export default {
  name: 'TSX',
  components: {
    Spinner,
    Tippy,
    Field
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
  created () {
    // this.updateFields()
  },
  mounted () {
    Chart.defaults.font.size = 14
    this.createMonitoringConsistencyPlot()
    this.createSummaryPlot()
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
  computed: {
    sidebarFields() {
      return this.fields.filter(f => f.name != 'refyear')
    },
    referenceYearField() {
      return this.fields.filter(f => f.name == 'refyear')[0]
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
  methods: {
    // reset() {
    //   this.fieldValues = { type: this.fieldValues.type }
    // },
    noDataMessage() {
      if(this.fieldValues && this.fieldValues.type == 'individual') {
        return "(Please select a species)"
      } else {
        return "(No data to show)"
      }
    },
    updateFields() {
      let params = {
        dataset: dataset,
        ...this.fieldValues
      }

      api.visualisationParameters(params).then(result => {
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
      var data = {
        labels: [],
        datasets: [{
          label: 'TSX',
          borderColor: '#36699e',
          backgroundColor: 'black',
          fill: false,
          pointRadius: 0,
          lineTension: 0,
          data: []
        }, {
          label: 'Confidence Interval (low)',
          backgroundColor: 'rgba(230,230,230,0.5)',
          fill: false,
          pointRadius: 0,
          lineTension: 0,
          borderColor: '#0000',
          borderWidth: 1,
          data: []
        }, {
          label: 'Confidence Interval (high)',
          // backgroundColor: '#eee',
          backgroundColor: 'rgba(230,230,230,0.5)',
          fill: 1, // Fill between this dataset and dataset[1], i.e. between low & hi CI
          pointRadius: 0,
          lineTension: 0,
          borderColor: '#0000',
          borderWidth: 0,
          data: []
        }]
      }

      this.mainIndexPlot = new Chart(this.$refs.lpiplot.getContext('2d'), {
        type: 'line',
        data: data,
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false
            }
          },
          maintainAspectRatio: false,
          scales: {
            yAxis: {
              display: true,
              position: 'left',
              grid: {
                display: true
              },
              ticks: {
                callback: function(label, index, labels) {
                  // Force labels to always show one decimal place
                  return (+label).toFixed(1)
                }
              }
            }
          }
        }
      })
    },
    updateMainIndexPlot(params) {
      let plotData = this.mainIndexPlot.data
      plotData.labels = []
      plotData.datasets.forEach(x => x.data = [])

      this.trendData = null

      var token = this.updateMainIndexPlot.token = {}
      var stale = () => this.updateMainIndexPlot.token != token

      return api.trend(params).then((data) => {
        if(stale()) {
          return
        }
        if(data) {
          this.trendData = data

          plotData.labels = data.year
          plotData.datasets[0].data = data.value
          plotData.datasets[1].data = data.low
          plotData.datasets[2].data = data.high

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
              }
            },
            xAxis: {
              type: 'linear',
              ticks: {
                callback: (label, index, labels) => '' + label
              }
            }
          }
        }
      })
    },
    createSummaryPlot() {
      this.summaryPlotData = {
        datasets: [{
          label: 'Number of taxa',
          xAxisID: 'year',
          yAxisID: 'numTaxa',
          borderColor: '#58899e',
          backgroundColor: '#58899e',
          data: []
        }, {
          label: 'Number of time series',
          xAxisID: 'year',
          yAxisID: 'numTimeSeries',
          borderColor: '#a3c489',
          backgroundColor: '#a3c489',
          data: []
        }]
      }
    },
    updateMonitoringConsistencyAndSummaryPlot(params) {
      this.monitoringConsistencyPlot.data.datasets.forEach(x => x.data = [])
      this.summaryPlotData.datasets.forEach(x => x.data = [])

      return api.diagnosticPlots(params).then((data) => {
          this.noData = data['dotplot'].length === 0

          var dotPlotData = data['dotplot']
          var plotData = this.monitoringConsistencyPlot.data

          dotPlotData.forEach(function(timeSeries, i) {
            timeSeries.forEach(function(value) {
              var year = value[0]
              var count = value[1]
              plotData.datasets[count === 0 ? 1 : 0].data.push({
                x: year,
                y: i + 1,
                r: 1
              })
            })
          })

          // summary plot
          var taxaCountData = data['summary']['taxa']
          var timeSeriesCountData = data['summary']['timeseries']
          var year = 0
          for (year in taxaCountData) {
            this.summaryPlotData.datasets[0].data.push({'x': +year, 'y': +taxaCountData[year]})
          }
          for (year in timeSeriesCountData) {
            this.summaryPlotData.datasets[1].data.push({'x': +year, 'y': +timeSeriesCountData[year]})
          }

          this.monitoringConsistencyPlot.update()
          this.refreshSummaryPlot() // note: this.summaryPlot.update() will cause exception as the axis might be change
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
        this.map.invalidateSize()
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
      var url = api.lpiDownloadURL(params)
      window.open(url)
    },
    downloadTrend: function(evt) {
      api.trend({ format: 'raw', ...this.dataParams}).then((data) => {
        saveTextFile(data, 'text/plain', "tsx-trend-" + this.filterFilenamePart + ".txt")
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
        dl.click();
      }

      async function save(name, params) {
        var data = await fetch("https://tsx.org.au/tsxapi/lpi-data/plot?" + params)
        var json = await data.json();

        var rows = json.dotplot.flatMap((a, i) => [a.map(b => [i, b[0], b[1]])]).flat()
        rows = [["TimeSeries", "Year", "NonZeroCount"]].concat(rows)

        download(csv(rows), "tsx-dotplot-" + name + ".csv");

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
    // refresh summary plot
    refreshSummaryPlot: function() {
      if (this.summaryPlot) {
        this.summaryPlot.destroy()
      }
      // create new one
      this.summaryPlot = new Chart(this.$refs.sumplot.getContext('2d'), {
        type: 'scatter',
        data: this.summaryPlotData,
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
                callback: (label, index, labels) => '' + label
              }
            },
            numTaxa: {
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
            },
            numTimeSeries: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Number of time series'
              },
              grid: {
                display: false
              },
              ticks: {
                callback: function(label, index, labels) {
                  return Number.isInteger(label) ? label.toLocaleString() : ''
                }
              }
            }
          }
        }
      })
    }
  }
}
</script>

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

  .info-icon {
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
  @media screen and (min-width: 768px) {
    .ie11-bugfix {
      /* Fix flexbox bug */
      height: 48em;
    }
  }
</style>

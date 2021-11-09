<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Data Subset Download</h2>
          <h3 class="title is-5">1. Subset Criteria</h3>

          <p style="margin-bottom: 1em;">Data that meets <em>all</em> of the criteria selected below will be included in the subset download.</p>

          <form>
            <fieldset v-bind:disabled="submitting">
              <div class="field">
                <label class="label">State/Territory</label>
                <div class="control">
                  <div class="select">
                    <select v-model="criteria.state">
                      <option v-bind:value="null" selected>All States and Territories</option>
                      <option v-for="s in options.state" v-bind:value="s">
                        {{ s }}
                      </option>
                      <option>South Australia</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="field">
                <label class="label">Programs</label>
                <div class="control">
                  <div v-for="program in options.monitoringPrograms">
                    <label><input type="checkbox" v-bind:value="program" v-model="criteria.monitoringPrograms"> {{program.description}}</label>
                  </div>
                  <p style="margin-top: 1em; font-style: italic;" v-if="criteria.monitoringPrograms.length == 0">
                    At least one program must be selected
                  </p>
                </div>
              </div>
              <div class="field">
                <label class="label">Species</label>
                <div class="control">
                  <div class="select">
                    <select v-model="criteria.species">
                      <option v-bind:value="null" selected>All Species</option>
                      <option v-for="sp in options.species" v-bind:value="sp">
                        {{ sp.common_name || sp.scientific_name }} ({{sp.id}})
                      </option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div class="field">
                <label class="label">Intensive Management</label>
                <div class="control">
                  <div class="select">
                    <select v-model="criteria.intensiveManagement">
                      <option v-bind:value="null" selected>All sites (managed & unmanaged)</option>
                      <option>Any management</option>
                      <option>Predator-free</option>
                      <option>Translocation</option>
                      <option>No known management</option>
                    </select>
                  </div>
                </div>
              </div> 
            </fieldset>
          </form>
          <hr>
          <div v-if="stats">
            Selected data subset contains
              {{formatQuantity(stats.sighting_count, "record")}} and
              {{formatQuantity(stats.taxon_count, "taxon", "taxa")}}.
          </div>
          <div v-else style="font-style: italic;">
              Loading...
              <spinner size='small' style='display: inline-block;'></spinner>
          </div>
          <hr>
          <h3 class="title is-5">2. Download Data Subset</h3>
          <div>
            <button type="button" class="button is-primary" style="margin: 0.5em 0;"
              v-on:click="downloadRawData"
              v-bind:disabled="!enableDownload">Download Raw Data (CSV format)</button>
          </div>
          <div>
            <button type="button" class="button is-primary" style="margin: 0.5em 0;"
              v-on:click="downloadTimeSeries"
              v-bind:disabled="!enableDownload">Download Time Series (CSV format)</button>
          </div>
          <hr>
          <div v-if="trendStatus == 'idle'">
            <button type="button" class="button is-primary" style="margin: 0.5em 0;"
              v-on:click="generateTrend"
              v-bind:disabled="!enableDownload">Generate Population Trend</button>
          </div>
          <div v-if="trendStatus == 'processing'">
            Please wait while the population trend is generated. This may take several minutes.
            <spinner size='small' style='display: inline-block;'></spinner>
          </div>
          <div v-if="trendStatus == 'error'">
            An error occurred while generating the trend. Please try again later, or contact james@planticle.com.au for assistance.
          </div>
          <div v-if="trendStatus == 'ready'">
            <h4 class="title is-6" style="margin: 1em 0;">Population Trend</h4>
            <p style="margin: 1em 0; font-style: italic;">Note: This trend has been generated using the Living Planet Index methodology, which is designed for producing composite trends, not single-species trends.</p>
            <p style="margin: 1em 0">
              <button type="button" class="button is-primary" style="margin: 0.5em 0;" v-on:click="downloadTrend">Download Population Trend (TXT format)</button>
            </p>
            <canvas v-show="showPlot" ref="plot" style="height: 10em;"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'
// import Spinner from 'vue-simple-spinner'
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
} from 'chart.js';

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
);


export default {
  name: 'DataSubsetDownloads',
  components: {
    Spinner
  },
  data () {
    return {
      status: 'loading',
      trendStatus: 'idle',
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
        monitoringPrograms: [],
        species: []
      },
      criteria: {
        state: null,
        monitoringPrograms: [],
        species: null,
        intensiveManagement: null
      },
      changeCounter: 0, // Incremented every time criteria are changed
      stats: null
    }
  },
  computed: {
    submitting: function() {
      return this.status === 'submitting'
    },
    enableDownload: function() {
      return this.criteria.monitoringPrograms.length > 0
    }
  },
  watch: {
    criteria: {
      handler() {
        var params = this.buildDownloadParams()
        this.stats = null
        api.dataSubsetStats(params).then(stats => {
          this.stats = stats
        })
        this.changeCounter++
        this.trendStatus = 'idle'
        this.showPlot = false
      },
      deep: true
    }
  },
  created () {
    Promise.all([
      api.currentUser().then((user) => {
        this.user = user
        if(user.is_admin) {
          return api.monitoringPrograms()
        } else {
          return api.programsManagedBy(user.id)
        }
      }).then((programs) => {
        this.options.monitoringPrograms = programs
        this.criteria.monitoringPrograms = programs // select all by default
      }),
      api.species({ q: 't1_present' }).then((species) => {
        this.options.species = species
      })
    ]).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
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
      let params = this.buildDownloadParams()
      let v = this.changeCounter // used to detect if parameters are changed during trend generation
      api.dataSubsetGenerateTrend(params).then(x => {
        this.trendId = x.id
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrendStatus(x.id, v), 3000)
      })
    },
    checkTrendStatus: function(id, v) {
      if(v != this.changeCounter) {
        return
      }
      api.dataSubsetTrendStatus(id).then(x => {
        if(x.status == 'ready') {
          this.trendStatus = 'ready'
          this.trendDownloadURL = api.dataSubsetTrendDownloadURL(id)
          
          setTimeout(() => this.plotTrend(id, v), 0, id);
        } else if(x.status == 'processing') {
          setTimeout(() => this.checkTrendStatus(id, v), 3000)
        }
      }).catch(e => {
        console.log(e);
        this.trendStatus = 'error'
      });
    },
    downloadTrend() {
      window.location = this.trendDownloadURL
    },
    plotTrend(id, v) {
      api.dataSubsetTrend(id).then(data => {
        if(v != this.changeCounter) {
          return
        }
        let series = data.split('\n')
            .slice(1) // Ignore first line
            .filter(line => line.trim().length > 0 && !/NA/.test(line)) // Ignore empty or NA lines
            .map(line => line.split(' '))

        let labels = series.map(x => parseInt(x[0].replace(/"/g, '')))
        let index = series.map(x => parseFloat(x[1]))
        let lowerCI = series.map(x => parseFloat(x[2]))
        let upperCI = series.map(x => parseFloat(x[3]))

        let plotData = {
          labels: labels,
          datasets: [{
            label: 'TSX',
            borderColor: '#36699e',
            backgroundColor: 'black',
            fill: false,
            pointRadius: 0,
            lineTension: 0,
            data: index
          }, {
            label: 'Confidence Interval (low)',
            backgroundColor: 'rgba(230,230,230,0.5)',
            fill: false,
            pointRadius: 0,
            lineTension: 0,
            borderColor: '#0000',
            borderWidth: 1,
            data: lowerCI
          }, {
            label: 'Confidence Interval (high)',
            // backgroundColor: '#eee',
            backgroundColor: 'rgba(230,230,230,0.5)',
            fill: 1, // Fill between this dataset and dataset[1], i.e. between low & hi CI
            pointRadius: 0,
            lineTension: 0,
            borderColor: '#0000',
            borderWidth: 0,
            data: upperCI
          }]
        }

        this.showPlot = true

        let plot = new Chart(this.$refs.plot.getContext('2d'), {
          type: 'line',
          data: plotData,
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false
              }
            },
            maintainAspectRatio: true,
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
      })
    },
    buildDownloadParams: function() {
      var params = {
        monitoring_programs: this.criteria.monitoringPrograms.map(x => x.id)
      }

      if(this.criteria.state) {
        params.state = this.criteria.state
      }

      if(this.criteria.intensiveManagement) {
        params.intensive_management = this.criteria.intensiveManagement
      }

      if(this.criteria.species) {
        params.taxon_id = this.criteria.species.id
      }

      return params
    },
    formatQuantity: function(x, singular, plural) {
      plural = plural || singular + "s"
      if(x == 0) {
        return "no " + plural
      } else if(x == 1) {
        return x + " " + singular
      } else {
        return x + " " + plural
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

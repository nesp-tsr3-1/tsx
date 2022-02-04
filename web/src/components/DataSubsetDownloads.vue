<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Data Subset Download</h2>
          <h3 class="title is-5">1. Subset Criteria</h3>

          <p style="margin-bottom: 1em;">Data that meets <em>all</em> of the criteria selected below will be included in the subset download.</p>
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
              <Multiselect
                    mode="multiple"
                    v-model="criteria.species"
                    :options="options.species"
                    :searchable="true"
                    placeholder="All species"
                    track-by="label"
                    value-prop="id"
                    label="label"
                    />
              </div>
              <div class="buttons" style="margin-top: 1em;">
                <button class="button is-small is-light" v-on:click="importSpeciesList">Import List</button>
                <button v-if="criteria.species.length" class="button is-small is-light" v-on:click="exportSpeciesList">Export List</button>
              </div>
              <table style="border: 1px solid #ccc;" class="table is-narrow" v-if="criteria.species.length">
                <thead>
                  <tr>
                    <th>Common name</th>
                    <th>Scientific name</th>
                    <th>ID</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="speciesId in criteria.species">
                    <td>{{speciesById(speciesId).common_name}}</td>
                    <td>{{speciesById(speciesId).scientific_name}}</td>
                    <td>{{speciesId}}</td>
                    <td><button class="delete is-small" style="margin-top: 4px" v-on:click="deselectSpecies(speciesId)"></button></td>
                  </tr>
                </tbody>
              </table>
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
          <hr>
          <div v-if="stats">
            Selected data subset contains
              {{formatQuantity(stats.sighting_count, "individual survey count")}},
              {{formatQuantity(stats.taxon_count, "taxon", "taxa")}},
              {{formatQuantity(stats.source_count, "dataset")}} and approx.
              {{formatQuantity(stats.time_series_count, "time series", "time series")}}.
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
            An error occurred while generating the trend.
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
import Multiselect from '@vueform/multiselect'
import { plotTrend } from '../plotTrend.js'

export default {
  name: 'DataSubsetDownloads',
  components: {
    Spinner,
    Multiselect
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
        species: [],
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
      return this.criteria.monitoringPrograms.length > 0 && this.stats && this.stats.sighting_count > 0
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
        this.options.species = species.map(sp => ({ ...sp, label: (sp.common_name || sp.scientific_name) + " (" + sp.id + ")" }))
      })
    ]).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
    speciesById: function(id) {
      return this.options.species.filter(x => x.id === id)[0]
    },
    deselectSpecies: function(id) {
      this.criteria.species = this.criteria.species.filter(x => x !== id)
    },
    importSpeciesList: function() {
      var self = this
      var input = document.createElement("input")
      input.type = "file"
      input.accept = "text/plain, text/csv"
      input.addEventListener("change", function(evt) {
        var file = input.files[0]
        var reader = new FileReader()
        reader.readAsText(file)
        reader.onload = function() {
          self.processSpeciesList(reader.result)
        }
      });
      document.body.append(input)
      input.click()
    },
    processSpeciesList: function(text) {
      var ids = text
        .split(/[\n\r]/)
        .flatMap(x => x.split(","))
        .map(x => x.trim())
        .filter(x => x.match(/^[pmu_]+[0-9]+$/))
      this.criteria.species = ids
    },
    exportSpeciesList: function() {
      function sanitise(x) {
        return x.replace(/[,\n\"]/g, ' ')
      }

      var csv = this.criteria.species.map(id => {
        var sp = this.speciesById(id)
        return sanitise(sp.common_name || "") + "," + sanitise(sp.scientific_name || "") + "," + (sp.id)
      }).join("\n")

      // var csv = this.criteria.species.join("\n")

      var data = new Blob([csv], {type: 'text/csv'})
      var url = window.URL.createObjectURL(data)
      var link = document.createElement("a")
      link.href = url
      link.download = "species-list.csv"
      document.body.append(link)
      link.click()
      window.URL.revokeObjectURL(url)
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
      let params = this.buildDownloadParams()
      let v = this.changeCounter // used to detect if parameters are changed during trend generation
      this.trendStatus = 'processing'
      api.dataSubsetGenerateTrend(params).then(x => {
        this.trendId = x.id
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrendStatus(x.id, v), 3000)
      }).catch(e => {
        console.log(e)
        this.trendStatus = 'error'
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
          
          setTimeout(() => this.plotTrend(id, v), 0, id)
        } else if(x.status == 'processing') {
          setTimeout(() => this.checkTrendStatus(id, v), 3000)
        }
      }).catch(e => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    downloadTrend() {
      window.location = this.trendDownloadURL
    },
    plotTrend(id, v) {
      api.dataSubsetTrend(id).then(data => {
        if(v != this.changeCounter) {
          return
        }
        this.showPlot = true
        plotTrend(data, this.$refs.plot)
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

      if(this.criteria.species && this.criteria.species.length > 0) {
        params.taxon_id = this.criteria.species.join(",")
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

<style>
.multiselect-search { height: 100%; } /* Fixes alignment issue with multiselect component */
</style>
<style src="@vueform/multiselect/themes/default.css"></style>

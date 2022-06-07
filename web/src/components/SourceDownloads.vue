<template>
  <div>
    <label class="label">Filtering criteria for downloads</label>
    <div v-if="enableFilter" style="margin-bottom: 1em; margin-left:  0.3em; border-left: 2px solid #eee; padding-left: 1em;">
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
                >
          </Multiselect>

          <div style="border-left: 2px solid #eee; padding-left: 1em;">
            <div class="buttons" style="margin-top: 1em;">
              <button class="button is-small is-light" v-on:click="importSpeciesList">Import List</button>
              <button v-if="criteria.species.length" class="button is-small is-light" v-on:click="exportSpeciesList">Export List</button>
              <tippy class="info-icon icon" arrow interactive placement="right" style="margin-bottom: 0.5rem;">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content content has-text-white">
                      <p>The list of selected species can be imported from a file in CSV format.</p>
                      <p>The file must have a column named <em>TaxonID</em> containing the taxon ID of each species. (Other columns are ignored.)</p>
                      <p>A full list of taxon IDs can be found in the <a href="http://tsx.org.au/files/TaxonList.xlsx">Taxon List</a>.</p>
                  </div>
                </template>
              </tippy>
            </div>
            <table style="border: 1px solid #ccc;" class="table is-narrow" v-if="criteria.species.length">
              <thead>
                <tr>
                  <th>Common name</th>
                  <th>Scientific name</th>
                  <th>Taxon ID</th>
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
        </div>
      </div>
      <div class="field">
        <label class="label">Sites</label>
        <div class="control">
          <Multiselect
            mode="multiple"
            v-model="criteria.sites"
            :options="querySites"
            :delay="500"
            :searchable="true"
            :close-on-select="false"
            :filter-results="false"
            no-options-text="No sites found"
            placeholder="All sites"
            label="name"
            value-prop="id"
            @open="(select) => select.refreshOptions()">
          </Multiselect>
        </div>
        <div style="border-left: 2px solid #eee; padding-left: 1em; margin-top: 1em">
                <table style="border: 1px solid #ccc;" class="table is-narrow" v-if="criteria.sites.length">
                  <thead>
                    <tr>
                      <th>Site name</th>
                      <th>Site ID</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="siteInfo in criteria.sites">
                      <td>{{siteInfo.split(',')[1]}}</td>
                      <td>{{siteInfo.split(',')[0]}}</td>
                      <td><button class="delete is-small" style="margin-top: 4px" v-on:click="deselectSite(siteInfo)"></button></td>
                    </tr>
                  </tbody>
                </table>
              </div>
      </div>
    </div>
  </div>
  <div>
    <button type="button" class="button is-primary" style="margin: 0.5em 0;"
    v-on:click="downloadRawData">Download Raw Data (CSV format)</button>
  </div>
  <div>
    <button type="button" class="button is-primary" style="margin: 0.5em 0;"
    v-on:click="downloadTimeSeries">Download Time Series (CSV format)</button>
  </div>
  <div v-if="trendStatus == 'idle'">
    <button type="button" class="button is-primary" style="margin: 0.5em 0;"
      v-on:click="generateTrend">Generate Population Trend</button>
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
    <p style="margin: 1em 0; font-style: italic;">Note: Population trends are generated from your time-series data using the Living Planet Index methodology. To find out more on how these trends are generated see the ‘TSX Dataset Downloads Factsheet’ above.</p>
    <p style="margin: 1em 0">
      <button type="button" class="button is-primary" style="margin: 0.5em 0;" v-on:click="downloadTrend">Download Population Trend (TXT format)</button>
    </p>
    <canvas v-show="showPlot" ref="plot" style="height: 10em;"></canvas>
  </div>
</template>

<script>
import * as api from '../api.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'
import { plotTrend } from '../plotTrend'
import Multiselect from '@vueform/multiselect'
import { readTextFile, extractSpeciesIDsFromCSV, saveTextFile, generateSpeciesCSV } from '../util.js'
import { Tippy } from 'vue-tippy'

export default {
  name: 'SourceDownloads',
  components: {
    Spinner,
    Multiselect,
    Tippy
  },
  data () {
    return {
      trendStatus: 'idle',
      trendDownloadURL: null,
      showPlot: false,
      enableFilter: true,
      options: {
        species: []
      },
      criteria: {
        species: [],
        sites: []
      }
    }
  },
  computed: {
  },
  created() {
    api.species({ source_id: this.sourceId }).then((species) => {
      function label(sp) {
        return sp.scientific_name + " (" + (sp.common_name ? (sp.common_name + ", ") : "") + sp.id + ")";
      }

      this.options.species = species.map(sp => ({ ...sp, label: label(sp) }))
    })
  },
  methods: {
    buildDownloadParams() {
      let params = { source_id: this.sourceId }
      if(this.enableFilter) {
        if(this.criteria.species && this.criteria.species.length > 0) {
          params.taxon_id = this.criteria.species.join(",")
        }
        if(this.criteria.sites && this.criteria.sites.length > 0) {
          params.site_id = this.criteria.sites.map(x => x.split(',')[0]).join(",")
        }
      }
      return params
    },
    downloadTimeSeries() {
      window.location = api.dataSubsetDownloadURL('time_series', this.buildDownloadParams())
    },
    downloadRawData() {
      window.location = api.dataSubsetDownloadURL('raw_data', this.buildDownloadParams())
    },
    generateTrend: function() {
      this.trendStatus = 'processing'
      api.dataSubsetGenerateTrend(this.buildDownloadParams()).then(x => {
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrendStatus(x.id), 3000)
      }).catch(e => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    checkTrendStatus: function(id) {
      api.dataSubsetTrendStatus(id).then(x => {
        if(x.status == 'ready') {
          this.trendStatus = 'ready'
          this.trendDownloadURL = api.dataSubsetTrendDownloadURL(id)
          setTimeout(() => this.plotTrend(id), 0)
        } else if(x.status == 'processing') {
          setTimeout(() => this.checkTrendStatus(id), 3000)
        }
      }).catch(e => {
        console.log(e)
        this.trendStatus = 'error'
      })
    },
    plotTrend(id) {
      api.dataSubsetTrend(id).then(data => {
        this.showPlot = true
        plotTrend(data, this.$refs.plot)
      })
    },
    downloadTrend() {
      window.location = this.trendDownloadURL
    },
    querySites: function(query) {
      let params = this.buildDownloadParams()
      delete params.site_id
      params.site_name_query = query || ""
      return api.dataSubsetSites(params)
        .then(sites => sites.map(site => ({ name: site.name, id: site.id + "," + site.name })))
    },
    importSpeciesList: function() {
      readTextFile("text/plain, text/csv", (text) => {
        this.criteria.species = extractSpeciesIDsFromCSV(text)
      })
    },
    exportSpeciesList: function() {
      var species = this.criteria.species.map(id => this.speciesById(id))
      var csv = generateSpeciesCSV(species)
      saveTextFile(csv, 'text/csv', 'species-list.csv')
    },
    speciesById: function(id) {
      return this.options.species.filter(x => x.id === id)[0]
    },
    deselectSpecies: function(id) {
      this.criteria.species = this.criteria.species.filter(x => x !== id)
    },
    deselectSite: function(site) {
      this.criteria.sites = this.criteria.sites.filter(x => x != site)
    },

  },
  props: {
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

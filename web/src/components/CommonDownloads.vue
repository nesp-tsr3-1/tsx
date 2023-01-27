<template>
  <slot name="criteria-title"></slot>
  <fieldset class="block" :disabled="submitting" :class="{ sideborder: sourceId }">
    <div class="field" v-if="enableStateFilter">
      <label class="label">State/Territory</label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.state">
            <option :value="null" selected>All States and Territories</option>
            <option v-for="s in options.state" :value="s">
              {{ s }}
            </option>
          </select>
        </div>
      </div>
    </div>
    <div class="field" v-if="enableProgramFilter">
      <label class="label">Programs</label>
      <div class="control">
        <div v-for="program in options.monitoringPrograms">
          <label><input type="checkbox" :value="program" v-model="criteria.monitoringPrograms" :disabled="isProgramDisabled(program)"> {{program.description}}</label>
        </div>
        <p style="margin-top: 1em; font-style: italic;" v-if="criteria.monitoringPrograms.length == 0">
          At least one program must be selected
        </p>
      </div>
    </div>
    <div class="field" v-if="enableTaxonomicGroupFilter">
      <label class="label">Taxonomic Group</label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.taxonomicGroup">
            <option :value="null" selected>All</option>
            <option v-for="s in options.taxonomicGroup" :value="s">
              {{ s }}
            </option>
          </select>
        </div>
      </div>
    </div>
    <div class="field">
      <label class="label">Species</label>
      <div class="control">
      <Multiselect
        mode="multiple"
        v-model="criteria.species"
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
        <div class="buttons" style="margin-top: 1em;">
          <button class="button is-small is-light" @click="importSpeciesList">Import List</button>
          <button v-if="criteria.species.length" class="button is-small is-light" @click="exportSpeciesList">Export List</button>
          <tippy class="info-icon icon" arrow interactive placement="right" style="margin-bottom: 0.5rem;">
            <template #default><i class="far fa-question-circle"></i></template>
            <template #content>
              <div class="popup-content content has-text-white">
                  <p>A list of selected species can be imported from a file in CSV format.</p>
                  <p>The file must contain a column named <em>TaxonID</em> listing the taxon ID of each species.</p>
                  <p>A full list of taxon IDs can be found in the <a href="https://tsx.org.au/files/TaxonList.xlsx" download>Taxon List</a>.</p>
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
              <td><button class="delete is-small" style="margin-top: 4px" @click="deselectSpecies(speciesId)"></button></td>
            </tr>
          </tbody>
        </table>
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
          @open="(select) => select.refreshOptions()"
          />
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
              <td><button class="delete is-small" style="margin-top: 4px" @click="deselectSite(siteInfo)"></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="field" v-if="enableManagementFilter">
      <label class="label">Management
        <tippy class="info-icon icon" arrow interactive placement="right" style="margin-bottom: 0.5rem;">
          <template #default><i class="far fa-question-circle"></i></template>
          <template #content>
            <div class="popup-content content has-text-white" style="font-weight: normal;">
                <p>The ‘No known management’ filtering option includes sites that fall into the ‘No management’ and ‘Unknown’ categories from the TSX data import template.</p>
            </div>
          </template>
        </tippy>
      </label>
      <div class="control">
        <div class="select">
          <select v-model="criteria.management">
            <option :value="null" selected>All sites (managed & unmanaged)</option>
            <option>Actively managed</option>
            <option>No known management</option>
          </select>
        </div>
      </div>
    </div>
  </fieldset>
  <div class="notification" v-if="stats">
    Selected data subset contains
      {{formatQuantity(stats.sighting_count, "individual survey count")}},
      {{formatQuantity(stats.taxon_count, "taxon", "taxa")}},
      {{formatQuantity(stats.source_count, "dataset")}} and approx.
      {{formatQuantity(stats.time_series_count, "time series", "time series")}}.
  </div>
  <div v-else class="notification" >
      Loading...
      <spinner size='small' style='display: inline-block;'></spinner>
  </div>

  <div v-if="enableMap" class="block" style="width: 100%; max-width: 640px; height: 480px; display: block; background: #eee;">
    <HeatMap :heatmap-data="heatmapData" :loading="heatmapLoading"></HeatMap>
  </div>

  <slot name="downloads-title"></slot>

  <div class="block">
    <button type="button" class="button is-primary"
      @click="downloadRawData"
      :disabled="!enableDownload">Download Raw Data (CSV format)</button>
  </div>
  <div class="block">
    <button type="button" class="button is-primary"
      @click="downloadTimeSeries"
      :disabled="!enableDownload">Download Time Series (CSV format)</button>
  </div>
  <div v-if="trendStatus == 'idle'" class="block">
    <button type="button" class="button is-primary"
      @click="generateTrend"
      :disabled="!enableDownload">Generate Population Trend</button>
  </div>
  <div v-if="trendStatus == 'processing'" class="block">
    Please wait while the population trend is generated. This may take several minutes.
    <spinner size='small' style='display: inline-block;'></spinner>
  </div>
  <div v-if="trendStatus == 'error'" class="block">
    An error occurred while generating the trend.
  </div>
  <div v-if="trendStatus == 'ready'" class="content">
    <h4 class="title is-6">Population Trend</h4>
    <p style="font-style: italic;">Note: This trend has been generated using the Living Planet Index methodology, which is designed for producing composite trends, not single-species trends.</p>
    <p>
      <button type="button" class="button is-primary" @click="downloadTrend">Download Population Trend (TXT format)</button>
    </p>
    <canvas v-show="showPlot" ref="plot" style="height: 10em;"></canvas>
  </div>
</template>

<script>
import * as api from '../api.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'
import Multiselect from '@vueform/multiselect'
import HeatMap from './HeatMap.vue'
import { plotTrend } from '../plotTrend.js'
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
        taxonomicGroup: [],
        species: []
      },
      sitesLoading: false,
      criteria: {
        state: null,
        monitoringPrograms: [],
        species: [],
        sites: [],
        management: null,
        taxonomicGroup: null
      },
      changeCounter: 0, // Incremented every time criteria are changed
      stats: null,
      heatmapLoading: false,
      heatmapData: []
    }
  },
  computed: {
    submitting: function() {
      return this.status === 'submitting'
    },
    enableDownload: function() {
      return (!this.enableProgramFilter || this.criteria.monitoringPrograms.length > 0) && this.stats && this.stats.sighting_count > 0
    }
  },
  watch: {
    criteria: {
      handler() {
        // Update programs first if necessary
        if(this.enableProgramFilter) {
          let selectedProgramIds = this.criteria.monitoringPrograms.map(p => p.id).sort()
          let anyProgramSelected = selectedProgramIds.includes('any')
          let noProgramSelected = selectedProgramIds.includes('none')
          if(anyProgramSelected) {
            let newPrograms = this.options.monitoringPrograms.filter(p => noProgramSelected || p.id !== 'none')
            let newProgramIds = newPrograms.map(p => p.id).sort()

            if(selectedProgramIds.join() != newProgramIds.join()) {
              this.criteria.monitoringPrograms = newPrograms
              return
            }
          }
        }

        this.changeCounter++
        this.updateStats()
        this.trendStatus = 'idle'
        this.showPlot = false
      },
      deep: true
    }
  },
  created () {
    let initialisationPromises = []

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
            programs = [{ description: "Any program", id: "any" }, { description: "No program", id: "none"}].concat(programs)
          }
          this.options.monitoringPrograms = programs
          this.criteria.monitoringPrograms = programs.filter(p => p.id != "none") // select all programs by default
        })
      )
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

    initialisationPromises.push(speciesPromise.then((species) => {
      species.forEach(sp => {
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
    deselectSpecies: function(id) {
      this.criteria.species = this.criteria.species.filter(x => x !== id)
    },
    deselectSite: function(site) {
      this.criteria.sites = this.criteria.sites.filter(x => x != site)
    },
    importSpeciesList: function() {
      readTextFile("text/plain, text/csv", (text) => {
        var ids = extractSpeciesIDsFromCSV(text)
        api.speciesForIDs(ids).then(species => {
          species.forEach(sp => {
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
      var params = {}

      if(this.sourceId) {
        params.source_id = this.sourceId
      }

      if(this.enableProgramFilter) {
        params.monitoring_programs = this.criteria.monitoringPrograms.map(x => x.id)
      }

      if(this.enableStateFilter && this.criteria.state) {
        params.state = this.criteria.state
      }

      if(this.enableManagementFilter && this.criteria.management) {
        params.management = this.criteria.management
      }

      if(this.criteria.species && this.criteria.species.length > 0) {
        params.taxon_id = this.criteria.species.join(",")
      }

      if(this.criteria.sites && this.criteria.sites.length > 0) {
        params.site_id = this.criteria.sites.map(x => x.split(',')[0]).join(",")
      }

      if(this.enableTaxonomicGroupFilter && this.criteria.taxonomicGroup) {
        params.taxonomic_group = this.criteria.taxonomicGroup
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
        return x.toLocaleString() + " " + plural
      }
    },
    isProgramDisabled: function(program) {
      if(program.id == 'any' || program.id == 'none') {
        return false
      } else {
        return this.criteria.monitoringPrograms.map(p => p.id).includes('any')
      }
    },
    querySites: function(query) {
      let params = this.buildDownloadParams()
      delete params.site_id
      params.site_name_query = query || ""
      return api.dataSubsetSites(params)
        .then(sites => sites.map(site => ({ name: site.name, id: site.id + "," + site.name })))
    },
    querySpecies: function(query) {
      let params = this.buildDownloadParams()
      delete params.taxon_id
      params.species_name_query = query || ""
      return api.dataSubsetSpecies(params)
        .then(species => species.map(sp => ({ ...sp, label: speciesLabel(sp) })))
    },
    updateStats: function() {
      this.stats = null
      var params = this.buildDownloadParams()
      let v = this.changeCounter
      api.dataSubsetStats(params).then(stats => {
        if(v === this.changeCounter) {
          this.stats = stats
        }
      })
      if(this.enableMap) {
        this.heatmapLoading = true
        api.dataSubsetIntensityMap(params).then(data => {
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
  },
  props: {
    sourceId: Number,
    enableProgramFilter: Boolean,
    enableStateFilter: Boolean,
    enableManagementFilter: Boolean,
    enableTaxonomicGroupFilter: Boolean,
    enableMap: Boolean
  }
}

function speciesLabel(sp) {
  return sp.scientific_name + " (" + (sp.common_name ? (sp.common_name + ", ") : "") + sp.id + ")"
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

<template>
  <div class="section">
    <div class="container is-widescreen source-view" v-if="source">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>

          <h2 class="title">{{ source.description }}</h2>

          <hr>

          <h4 class="title is-4">
            Dataset Details
            <router-link :to="{ name: 'SourceEdit', params: { id: sourceId }}" tag="button" class="button is-small">Edit</router-link>
          </h4>

          <div class="columns">
            <div class="column">
              <div style="margin-bottom: 1em;">
                <div style="font-weight: bold;">Data Provider</div>
                {{ source.provider || 'N/A' }}
              </div>

              <div style="margin-bottom: 1em;">
                <div style="font-weight: bold;">Authors</div>
                {{ source.authors || 'N/A' }}
              </div>

              <div v-if="hasMonitoringProgram" style="font-weight: bold;">Monitoring Program</div>
              <div v-if="hasMonitoringProgram">{{ source.monitoring_program }}</div>
            </div>
            <div class="column">
              <div style="margin-bottom: 1em;">
                <div style="font-weight: bold;">Contact Information</div>
                <div v-if="hasContactInfo">
                  {{ source.contact_name }}<br>
                  {{ source.contact_institution }}<br>
                  {{ source.contact_position }}<br>
                  {{ source.contact_email }}<br>
                  {{ source.contact_phone }}
                </div>
                <div style="font-style: italic" v-else>
                  None
                </div>
              </div>
            </div>
          </div>

          <hr>

          <div class="columns">
            <div class="column">
              <h4 class="title is-4">Custodians</h4>
              <p class="content">
                Custodians are users who have access to import data and edit details for this dataset.
              </p>
              <source-custodians v-bind:sourceId="sourceId"></source-custodians>
            </div>
          </div>

          <hr v-if="showDownloads">

          <div class="columns" v-if="showDownloads">
            <div class="column">
              <h4 class="title is-4">Downloads</h4>
              <div>
                <button type="button" class="button is-primary" style="margin: 0.5em 0;"
                v-on:click="downloadTimeSeries">Download Time Series (CSV format)</button>
              </div>
              <div>
                <button type="button" class="button is-primary" style="margin: 0.5em 0;"
                  v-bind:disabled="trendStatus != 'idle'" v-on:click="generateTrend">Download Population Trend (CSV format)</button>
                  <p style="font-style: italic; margin-top: 1em;">Note: Population trends are generated using the Living Planet Index methodology, which is designed for producing composite trends, not single-species trends.</p>
              </div>
              <div v-if="trendStatus == 'processing'">
                Please wait while the population trend is generated. This may take several minutes.
                <spinner size='small' style='display: inline-block;'></spinner>
              </div>
              <div v-if="trendStatus == 'error'">
                An error occurred while generating the trend.
              </div>
            </div>
          </div>

          <hr>

          <div class="columns">
            <div class="column">
              <h4 class="title is-4">Data Processing Notes</h4>

              <processing-notes v-bind:sourceId="sourceId"></processing-notes>
            </div>
          </div>

          <hr>

          <div class="columns">
            <div class="column">
              <h4 class="title is-4">Import History</h4>

              <import-list v-bind:sourceId="sourceId" ref="importList"></import-list>
            </div>
          </div>

          <hr>

          <div class="columns">
            <div class="column">
              <h4 class="title is-4">Import Data</h4>
            </div>
          </div>

          <import-data v-bind:sourceId="sourceId" v-on:data-import-updated="handleDataImportUpdated"></import-data>

          <hr>

          <h4 class="title is-6">Delete Dataset</h4>
          <p class="content">
            Deleting this dataset will remove it from the index and cannot be undone. All previously imported data and processing notes will be deleted.
          </p>
          <p class="content">
            If you wish to update your dataset, simply import an new file using the 'Import Data' section above.
          </p>
          <div class="field">
            <input type="checkbox" id="checkbox" v-model="enableDelete">
            <label for="checkbox"> I understand and wish to delete this dataset</label>
          </div>
          <button class='button is-danger' :disabled="!enableDelete" v-on:click='deleteSource'>Delete this dataset</button>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import ImportList from './ImportList.vue'
import ImportData from './ImportData.vue'
import ProcessingNotes from './ProcessingNotes.vue'
import SourceCustodians from './SourceCustodians.vue'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'

export default {
  name: 'SourceView',
  components: {
    'import-list': ImportList,
    'import-data': ImportData,
    'processing-notes': ProcessingNotes,
    'source-custodians': SourceCustodians,
    'spinner': Spinner
  },
  data () {
    return {
      sourceId: +this.$route.params.id,
      source: null,
      latestImportId: null,
      enableDelete: false,
      showDownloads: false,
      trendStatus: 'idle',
      trendDownloadURL: null
    }
  },
  computed: {
    hasContactInfo() {
      let source = this.source
      return !!(source && (source.contact_name || source.contact_institution || source.contact_position || source.contact_email || source.contact_phone))
    },
    hasMonitoringProgram() {
      let source = this.source
      return !!source.monitoring_program
    }
  },
  methods: {
    deleteSource() {
      api.deleteDataSource(this.sourceId).then(() => {
        this.$router.replace({ path: '/source' })
      }).catch(error => {
        console.log(error)
        alert('Delete failed.')
      })
    },
    handleDataImportUpdated() {
      this.$refs.importList.refresh()
      api.dataSource(this.sourceId).then(source => {
        this.showDownloads = source.has_t1_data
      })
    },
    downloadTimeSeries() {
      window.location = api.dataSubsetDownloadURL('time_series', { source_id: this.sourceId })
    },
    generateTrend: function() {
      api.dataSubsetGenerateTrend({ source_id: this.sourceId }).then(x => {
        this.trendStatus = 'processing'
        setTimeout(() => this.checkTrendStatus(x.id), 3000)
      })
    },
    checkTrendStatus: function(id) {
      api.dataSubsetTrendStatus(id).then(x => {
        if(x.status == 'ready') {
          this.trendStatus = 'idle'
          window.location = api.dataSubsetTrendDownloadURL(id)
        } else if(x.status == 'processing') {
          setTimeout(() => this.checkTrendStatus(id), 3000)
        }
      }).catch(e => {
        console.log(e);
        this.trendStatus = 'error'
      });
    }
  },
  created () {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    api.dataSource(this.sourceId).then(source => {
      this.source = source
      this.showDownloads = source.has_t1_data
    })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

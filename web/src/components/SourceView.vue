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
              <h4 class="title is-4">Downloads</h4>
              <p class="content" v-if="processedData.status == 'loading'">
                Loading
              </p>
              <p class="content" v-if="processedData.status == 'loaded'">
                <ul>
                  <li v-for="item in processedData.items"><a v-bind:href="itemURL(item)" target="_blank">{{item.name}}</a></li>
                </ul>
              </p>
              <p class="content" v-if="processedData.status == 'failed'">
                {{ processedData.error }}
              </p>
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
            <label for="checkbox">I understand and wish to delete this dataset</label>
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

export default {
  name: 'SourceView',
  components: {
    'import-list': ImportList,
    'import-data': ImportData,
    'processing-notes': ProcessingNotes,
    'source-custodians': SourceCustodians
  },
  data () {
    return {
      sourceId: +this.$route.params.id,
      source: null,
      latestImportId: null,
      enableDelete: false,
      processedData: { status: 'loading' }
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
    },
    itemURL(item) {
      return api.dataSourceProcessedDataItemURL(this.sourceId, item.id)
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
    })
    api.dataSourceProcessedData(this.sourceId).then(processedData => {
      this.processedData = { status: 'loaded', ...processedData }
    }).catch(e => {
      this.processedData = { status: 'failed', error: e }
    })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

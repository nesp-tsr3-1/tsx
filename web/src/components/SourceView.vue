<template>
  <div class="section">
    <div
      v-if="source"
      class="container is-widescreen source-view"
    >
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav />

          <h2 class="title">
            {{ source.description }}
          </h2>

          <div
            v-if="showNoDataAgreementMessage"
            class="notification is-danger is-light"
          >
            Note: There is currently no data sharing agreement in place for this dataset.
          </div>

          <hr>

          <h4 class="title is-4">
            Dataset Details
            <router-link :to="{ name: 'SourceEdit', params: { id: sourceId }}">
              <button class="button is-small">
                Edit
              </button>
            </router-link>
          </h4>

          <div class="columns is-multiline dataset-details">
            <div class="column is-half">
              <div>
                <h4>Data Details</h4>
                {{ source.details || 'N/A' }}
              </div>

              <div>
                <h4>Data Provider</h4>
                {{ source.provider || 'N/A' }}
              </div>

              <div>
                <h4>Authors</h4>
                {{ source.authors || 'N/A' }}
              </div>
            </div>
            <div class="column is-half">
              <div>
                <h4>Contact Information</h4>
                <div v-if="hasContactInfo">
                  {{ source.contact_name }}<br>
                  {{ source.contact_institution }}<br>
                  {{ source.contact_position }}<br>
                  {{ source.contact_email }}<br>
                  {{ source.contact_phone }}
                </div>
                <div
                  v-else
                  style="font-style: italic"
                >
                  None
                </div>
              </div>
            </div>
            <div class="column is-full">
              <div>
                <h4>Data Citation</h4>
                {{ citation || 'N/A' }}
              </div>
              <div v-if="hasMonitoringProgram">
                <h4>Monitoring Program</h4>
                {{ source.monitoring_program }}
              </div>
              <div>
                <h4>Source Type</h4>
                {{ sourceType }}
              </div>
              <div v-if="documentsEnabled">
                <h4>Agreement(s)</h4>
                {{ source.data_agreement_status_long_description }}
                <div
                  v-for="file in source.data_agreement_files"
                  :key="file.upload_uuid"
                >
                  <a :href="uploadURL(file.upload_uuid)">{{ file.filename }}</a>
                </div>
              </div>
            </div>
          </div>

          <hr>

          <h4
            id="summary_top"
            class="title is-4"
          >
            Dataset Summary
          </h4>

          <source-data-summary
            ref="dataSummary"
            :source-id="sourceId"
          />

          <div v-if="manageCustodiansPermitted">
            <hr>

            <div class="columns">
              <div class="column">
                <h4 class="title is-4">
                  Custodians
                </h4>
                <p class="content">
                  Custodians are users who have access to import data and edit details for this dataset.
                </p>
                <source-custodians :source-id="sourceId" />
              </div>
            </div>
          </div>

          <div v-if="showDownloads">
            <hr>

            <div class="columns">
              <div class="column">
                <h4 class="title is-4">
                  Downloads
                </h4>
                <div>
                  <a
                    href="/data/TSX%20Dataset%20Downloads%20Factsheet.pdf"
                    class="button is-dark"
                    target="_blank"
                    style="margin: 0.5em 0;"
                  >
                    TSX Dataset Downloads Factsheet
                  </a>
                </div>
                <hr>

                <source-downloads
                  :source-id="sourceId"
                  :enable-map="true"
                />
              </div>
            </div>
          </div>

          <div v-if="importDataPermitted">
            <hr>

            <div class="columns">
              <div class="column">
                <h4 class="title is-4">
                  Data Processing Notes
                </h4>

                <processing-notes :source-id="sourceId" />
              </div>
            </div>

            <hr>

            <div class="columns">
              <div class="column">
                <h4 class="title is-4">
                  Import History
                </h4>

                <import-list
                  ref="importList"
                  :source-id="sourceId"
                />
              </div>
            </div>

            <hr>

            <div class="columns">
              <div class="column">
                <h4 class="title is-4">
                  Import Data
                </h4>
              </div>
            </div>

            <import-data
              :source-id="sourceId"
              @data-import-updated="handleDataImportUpdated"
            />
          </div>

          <div v-if="deletePermitted">
            <hr>

            <h4 class="title is-6">
              Delete Dataset
            </h4>
            <p class="content">
              Deleting this dataset will remove it from the index and cannot be undone. All previously imported data, processing notes, and associated custodian feedback form data will be deleted.
            </p>
            <p class="content">
              If you wish to update your dataset, simply import an new file using the 'Import Data' section above.
            </p>
            <div class="field">
              <input
                id="checkbox"
                v-model="enableDelete"
                type="checkbox"
              >
              <label for="checkbox"> I understand and wish to delete this dataset</label>
            </div>
            <button
              class="button is-danger"
              :disabled="!enableDelete"
              @click="deleteSource"
            >
              Delete this dataset
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import features from '../features.js'
import { generateCitation, capitalise } from '../util.js'
import ImportList from './ImportList.vue'
import ImportData from './ImportData.vue'
import ProcessingNotes from './ProcessingNotes.vue'
import SourceCustodians from './SourceCustodians.vue'
import SourceDownloads from './SourceDownloads.vue'
import SourceDataSummary from './SourceDataSummary.vue'

export default {
  name: 'SourceView',
  components: {
    'import-list': ImportList,
    'import-data': ImportData,
    'processing-notes': ProcessingNotes,
    'source-custodians': SourceCustodians,
    'source-downloads': SourceDownloads,
    'source-data-summary': SourceDataSummary
  },
  data() {
    return {
      sourceId: +this.$route.params.id,
      source: null,
      latestImportId: null,
      enableDelete: false,
      showDownloads: false
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
    },
    deletePermitted() {
      return this.source && this.source.can_delete
    },
    importDataPermitted() {
      return this.source && this.source.can_import_data
    },
    manageCustodiansPermitted() {
      return this.source && this.source.can_manage_custodians
    },
    citation() {
      return this.source && generateCitation(this.source.authors, this.source.details, this.source.provider)
    },
    sourceType() {
      return capitalise(this.source.source_type ?? '')
    },
    documentsEnabled() {
      return features.documents
    },
    showNoDataAgreementMessage() {
      return this.documentsEnabled && this.source.show_no_agreement_message
    }
  },
  created() {
    api.isLoggedIn().then((isLoggedIn) => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    api.dataSource(this.sourceId).then((source) => {
      this.source = source
      this.showDownloads = source.has_t1_data
    })
  },
  methods: {
    deleteSource() {
      api.deleteDataSource(this.sourceId).then(() => {
        this.$router.replace({ path: '/source' })
      }).catch((error) => {
        console.log(error)
        alert('Delete failed.')
      })
    },
    handleDataImportUpdated() {
      this.$refs.importList.refresh()
      this.$refs.dataSummary.refresh()
      api.dataSource(this.sourceId).then((source) => {
        this.showDownloads = source.has_t1_data
      })
    },
    uploadURL: api.uploadURL
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.dataset-details {
  margin-top: 1.5em;
}
.dataset-details > .column {
  margin-top: -1.5em;
}
.dataset-details h4 {
  font-weight: bold;
}
.dataset-details > .column > div {
  margin-bottom: 1em;
}
</style>

<template>
  <div class="import-list">
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load imports.
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <p
        v-if="imports.length == 0"
        class="table is-fullwidth is-striped is-hoverable"
      >
        None
      </p>
      <table
        v-if="imports.length > 0"
        class="table is-fullwidth is-striped is-hoverable"
      >
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Uploaded</th>
            <th style="width: 4em;" />
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="i in imports"
            :key="i.id"
          >
            <td :title="i.filename">
              <div
                style="display: flex;
                flex-direction: column;
                gap: 0.5em;
                align-items: start;"
              >
                <div>
                  <span
                    v-if="i.data_type === 2"
                    class="tag is-danger"
                    style="margin-right: 0.5em"
                  >Type 2</span><a :href="importUrl(i)">{{ i.filename }}</a>
                </div>
                <div
                  v-if="isMostRecentImport(i)"
                  class="celltag"
                >
                  Most recent import – to update your dataset, download this file and add your new data.
                </div>
                <div
                  v-if="i.timeSeriesImportStatus == 'imported'"
                  class="celltag"
                >
                  Time series imported (<a :href="importUrl(i.time_series_import)">{{ i.time_series_import.filename }}</a>) at {{ formatDateTime(i.time_series_import.time_created) }} <span v-if="i.time_series_import.user">by {{ i.time_series_import.user }}</span>
                  (<span
                    class="link"
                    @click="function() { deleteTimeSeriesImport(i) }"
                  >delete</span>)
                </div>
                <div
                  v-if="i.timeSeriesImportError"
                  class="celltag tag is-danger"
                >
                  {{ i.timeSeriesImportError }}
                </div>
                <div
                  v-if="showImportTimeSeries(i)"
                >
                  <button
                    v-if="showImportButton(i)"
                    class="button is-small"
                    @click="function() { importTimeSeries(i) }"
                  >
                    Upload Time Series
                  </button>
                </div>
                <div
                  v-if="importStatusDescription(i)"
                >
                  {{ importStatusDescription(i) }}
                  <span class="loader" />
                </div>
              </div>
            </td>
            <td>
              {{ humanizeStatus(i.status) }}
              <a
                :href="importLogUrl(i)"
                target="_blank"
              >(log)</a>
              <button
                v-if="canApproveImport(i)"
                class="button is-small"
                :class="{ 'is-loading': i.isApproving }"
                @click="function() { approveImport(i) }"
              >
                Approve
              </button>
            </td>
            <td>{{ formatDateTime(i.time_created) }} by {{ i.user }}</td>
            <td class="visibility">
              <button
                v-if="canShowImport(i)"
                title="Hidden from custodians"
                :disabled="i.isUpdatingVisibility"
                @click="showImport(i)"
              >
                <img src="../assets/icons/visibility_off.svg">
              </button>
              <button
                v-if="canHideImport(i)"
                title="Visible to custodians"
                :disabled="i.isUpdatingVisibility"
                @click="hideImport(i)"
              >
                <img src="../assets/icons/visibility.svg">
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { humanizeStatus, formatDateTime, selectFiles } from '../util.js'

export default {
  name: 'ImportList',
  props: {
    sourceId: {
      type: Number,
      required: true
    }
  },
  data() {
    var data = {
      imports: [],
      status: 'loading',
      currentUser: null
    }

    return data
  },
  created() {
    api.currentUser().then((currentUser) => {
      this.currentUser = currentUser
    })
    this.refresh()
  },
  methods: {
    refresh() {
      var importsPromise = api.dataSourceImports(this.sourceId)
      importsPromise.then((imports) => {
        imports.forEach((i) => {
          i.isApproving = false
          i.isUpdatingVisibility = false
          i.timeSeriesImportStatus = i.time_series_import ? 'imported' : 'init'
        })
        this.imports = imports
        //   .sort((a, b) => b.time_created.localeCompare(a.time_created))
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    importUrl(i) {
      return api.uploadURL(i.upload_uuid)
    },
    importLogUrl(i) {
      return api.dataImportLogUrl(i.id)
    },
    approveImport(i) {
      i.isApproving = true

      if(i.status !== 'imported') {
        console.log('approveImport: unexpected status: ' + i.status)
        return
      }

      api.approveImport(i.id).then(() => {
        i.status = 'approved'
      }).catch((error) => {
        console.log(error)
      }).finally(() => {
        i.isApproving = false
      })
    },
    canApproveImport(i) {
      return this.currentUserCanApprove() && i.status === 'imported' && i === this.imports[0]
    },
    showImport(i) {
      i.isUpdatingVisibility = true
      api.showImport(i.id).then(() => {
        i.is_hidden = false
      }).catch((error) => {
        console.log(error)
      }).finally(() => {
        i.isUpdatingVisibility = false
      })
    },
    hideImport(i) {
      i.isUpdatingVisibility = true
      api.hideImport(i.id).then(() => {
        i.is_hidden = true
      }).catch((error) => {
        console.log(error)
      }).finally(() => {
        i.isUpdatingVisibility = false
      })
    },
    canShowImport(i) {
      return this.currentUserIsAdmin() && i.is_hidden
    },
    canHideImport(i) {
      return this.currentUserIsAdmin() && !i.is_hidden
    },
    isMostRecentImport(i) {
      return i == this.imports[0]
    },
    currentUserCanApprove() {
      return this.currentUserIsAdmin()
    },
    currentUserIsAdmin() {
      return this.currentUser !== null && this.currentUser.roles.some(x => x === 'Administrator')
    },
    showImportTimeSeries(i) {
      return i.data_type == 2 && (i.status == 'approved' || i.status == 'imported') && this.currentUserIsAdmin
    },
    showImportButton(i) {
      return i.timeSeriesImportStatus == 'init'
    },
    importStatusDescription(i) {
      if(i.timeSeriesImportStatus == 'uploading') {
        let formattedProgress = i.timeSeriesUploadProgress?.toLocaleString(undefined, {
          maximumFractionDigits: 1,
          minimumFractionDigits: 1
        })
        return 'Uploading (' + formattedProgress + '%)'
      }
      if(i.timeSeriesImportStatus == 'importing') {
        return 'Importing…'
      }
    },
    deleteTimeSeriesImport(i) {
      if(window.confirm('Are you sure you wish to delete this time series import?')) {
        api.deleteTimeSeriesImport(i.id)
          .then(() => this.refresh())
          .catch((error) => {
            console.log(error)
            alert('Delete failed')
            throw error
          })
      }
    },
    importTimeSeries(i) {
      selectFiles({
        accept: 'text/csv',
        multiple: false
      }).then((files) => {
        i.timeSeriesImportError = null
        if(files.length > 0) {
          i.timeSeriesImportStatus = 'uploading'
          i.timeSeriesUploadProgress = 0

          return api.upload(files[0], (progress) => {
            i.timeSeriesUploadProgress = progress * 100
          })
        }
      }).then((result) => {
        console.log(result)
        i.timeSeriesImportStatus = 'importing'
        return api.importTimeSeries({
          source_id: this.sourceId,
          data_import_id: i.id,
          upload_uuid: result.uuid
        })
      }).then(() => {
        this.refresh()
      }).catch((error) => {
        console.log(error)
        if(error.json?.check_error) {
          i.timeSeriesImportError = 'Error importing time series: ' + error.json?.check_error
        } else {
          i.timeSeriesImportError = 'Failed to import time series due to unexpected problem.'
        }
        i.timeSeriesImportStatus = 'init'
      })
    },
    humanizeStatus,
    formatDateTime
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .table {
    table-layout: fixed;
  }
  .table td:nth-child(1) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space:  nowrap;
  }
  .table th:nth-child(2) {
    width: 12em;
  }
  .table th:nth-child(3) {
    width: 12em;
  }
  .table tbody tr {
    cursor: pointer;
  }
  td.visibility button {
    appearance: none;
    background: none;
    border: none;
    cursor: pointer;
  }
  button:disabled {
    opacity: 0.5;
  }
  .celltag {
    background: hsl(0, 0%, 96%);
    color: hsl(0, 0%, 29%);
    font-size: 0.75rem;
    padding: 0.3em 0.75em;
    display: inline;
    white-space: normal;
    border-radius: 4px;
    margin-top: 0.3em;
  }
  .link {
    color: hsl(229, 53%, 53%);
  }
  .link:hover {
    color: #333;
  }
</style>

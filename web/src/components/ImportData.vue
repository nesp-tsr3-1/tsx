<!--
  Import component, embedded within data source page
-->
<template>
  <div class="import-edit content">
    <div
      v-if="canEdit"
      class="field"
    >
      <label class="label">Data type</label>
      <div class="select">
        <select v-model="dataType">
          <option :value="1">
            Type 1
          </option>
          <option :value="2">
            Type 2/3 (Advanced)
          </option>
        </select>
      </div>
    </div>

    <div class="field">
      <label class="label">Data file</label>
      <div v-if="status == &quot;init&quot;">
        <p>
          <button
            class="button"
            @click="selectFile"
          >
            Select file
          </button>
        </p>
        <p class="notification is-warning is-light">
          <strong>Important:</strong> Before updating your dataset, please ensure that all draft custodian feedback forms have been submitted. Importing new data will reset and permanently remove all drafted responses in the most recent form. All previously completed forms will also be archived.
        </p>
        <p class="notification is-info is-light">
          <strong>Tip:</strong> The import will run faster if records belonging to the same survey and site are grouped into contiguous rows instead of scattered throughout the file.
        </p>
      </div>

      <p v-if="uploading">
        Uploading
        <progress
          class="progress is-primary is-small"
          :value="uploadProgress"
          max="100"
        >
          {{ uploadProgress }}%
        </progress>
      </p>

      <p v-if="fileURL && filename && !uploading">
        File uploaded: <a :href="fileURL">{{ filename }}</a>
      </p>
    </div>

    <div v-if="processing">
      <p>
        Processing {{ progressString }}
        <progress
          class="progress is-primary is-small"
          :value="processingProgress"
          max="100"
        >
          {{ processingProgress }}%
        </progress>
      </p>
    </div>

    <div
      v-if="status == &quot;checked_ok&quot;"
      class="notification is-success"
    >
      👍 Looks good! No errors detected. Please review the log below before importing the data.
    </div>

    <p v-if="status == &quot;checked_ok&quot;">
      <button
        class="button is-primary"
        @click="importData"
      >
        Finish importing data
      </button>
      <button
        class="button"
        @click="selectFile"
      >
        Upload an edited file
      </button>
    </p>

    <div
      v-if="status == &quot;checked_error&quot;"
      class="notification is-warning"
    >
      ⚠️ Some issues were detected in the uploaded file. Please check the log below and then upload a new version for checking.
    </div>

    <div
      v-if="status == &quot;import_error&quot;"
      class="notification is-warning"
    >
      ⚠️ Something went wrong while importing data. Please check the log below.
    </div>

    <p v-if="status == &quot;checked_error&quot; || status == &quot;import_error&quot;">
      <button
        class="button"
        @click="selectFile"
      >
        Upload an edited file
      </button>
    </p>

    <div
      v-if="status == &quot;approved&quot; || status == &quot;imported&quot;"
      class="notification is-success"
    >
      🎉 All data has been imported without errors. See full import log below.
    </div>

    <div
      v-if="processingComplete"
      class="log"
    >
      <h5>Import log</h5>
      <code
        v-for="log in importLogs"
        :class="log.level"
        style="display: block"
      >
        {{ log.message }}
      </code>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import * as util from '../util.js'

export default {
  name: 'ImportData',
  props: {
    sourceId: Number
  },
  data () {
    return {
      uploading: false,
      uploadProgress: 0,
      fileUUID: null,
      dataType: 1,
      filename: null,
      processingProgress: 0,
      progressString: '',
      importLogs: [],
      status: 'init',
      importId: null,
      name: '',
      isDestroyed: false
    }
  },
  computed: {
    processing: function() {
      return ['importing', 'checking'].includes(this.status)
    },
    processingComplete: function() {
      return ['checked_ok', 'checked_error', 'imported', 'import_error', 'approved'].includes(this.status)
    },
    canEdit: function() {
      return ['init', 'checked_ok', 'checked_error', 'import_error'].includes(this.status)
    },
    canProcess: function() {
      return !!(this.name.trim() !== '' && this.fileUUID)
    },
    fileURL: function() {
      if(this.fileUUID) {
        return api.uploadURL(this.fileUUID)
      }
    },
    title: function() {
      return 'TSX Data Import – ' + (this.name || 'Untitled')
    }
  },
  created: function() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })

    api.dataSourceImports(this.sourceId).then(imports => {
      if(imports.length > 0) {
        var lastImport = imports[imports.length - 1]
        if(lastImport.status !== 'imported' && lastImport.status !== 'approved') {
          this.importId = lastImport.id
          this.monitorImport()
        }
      }
    })
  },
  methods: {
    destroyed: function() {
      this.isDestroyed = true
    },
    selectFile: function() {
      util.selectFiles({
        accept: 'application/vnd.ms-excel,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        multiple: false
      }).then((files) => {
        if(files.length > 0) {
          this.uploading = true

          return api.upload(files[0], (progress) => {
            this.uploadProgress = progress * 100
          }).then((result) => {
            this.fileUUID = result.uuid
          }).finally(() => {
            this.uploading = false
          })
        }
      }).then(() => {
        if(this.fileUUID) {
          this.checkData()
        }
      })
    },
    checkData: function() {
      this.processImport('checking')
    },
    importData: function() {
      this.processImport('importing')
    },
    processImport: function(status) {
      this.status = status
      this.processingProgress = 0

      var promise

      var dataImport = {
        upload_uuid: this.fileUUID,
        data_type: this.dataType,
        source_id: this.sourceId
      }

      if(this.importId) {
        dataImport.status = status
        promise = api.updateImport(this.importId, dataImport)
      } else {
        promise = api.createImport(dataImport)
      }

      promise.then((dataImport) => {
        this.importId = dataImport.id
        // Poll server for progress while import is running
        return this.monitorImport()
      })
    },
    monitorImport: function() {
      return poll(() => api.dataImport(this.importId), 1000, (dataImport) => {
        if(this.isDestroyed) return false

        if(dataImport.total_rows && dataImport.processed_rows) {
          this.processingProgress = dataImport.processed_rows * 100 / dataImport.total_rows
          this.progressString = dataImport.processed_rows.toLocaleString() + ' / ' + dataImport.total_rows.toLocaleString() + ' rows'
        }
        this.fileUUID = dataImport.upload_uuid
        this.name = dataImport.name
        this.filename = dataImport.filename
        this.status = dataImport.status
        this.dataType = dataImport.data_type || 1
        return dataImport.status === 'checking' || dataImport.status === 'importing'
      }).then((dataImport) => {
        this.$emit('data-import-updated')
        return api.dataImportLog(dataImport.id)
      }).then((importLog) => {
        var logs = []

        importLog.split('\n').forEach((line) => {
          if(line.length > 0) {
            logs.push({
              message: line,
              level: line.indexOf('ERROR') >= 0 ? 'error' : line.indexOf('WARNING') >= 0 ? 'warning' : line.indexOf('INFO') >= 0 ? 'info' : null
            })
          }
        })

        this.importLogs = logs
      })
    },
    deleteImport: function() {
      if(confirm('Delete import - are you sure?')) {
        api.deleteImport(this.importId).then(() => {
          this.$router.push('/')
        }).catch((e) => {
          alert('Delete failed')
          return e
        })
      }
    }
  }
}

function delayPromise(ms, promiseFn) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(promiseFn()), ms)
  })
}

// Repeatedly polls promises generated by 'promiseFn', as long as 'callback' returns true on the promise result
function poll(promiseFn, delay, callback) {
  return promiseFn().then((result) => {
    if(callback(result)) {
      return delayPromise(delay, () => poll(promiseFn, delay, callback))
    } else {
      return result
    }
  })
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang='scss'>
@import '../../node_modules/bulma/sass/utilities/initial-variables.sass';
.log { color: #888; }
.error { color: $red; }
.info { color: $blue; }
.warning { color: orange; }


.log code {
  background: #eee;
}
// code {
//   background: white !important;
// }

</style>

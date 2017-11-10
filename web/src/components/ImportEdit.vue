<template>
  <div class="import-edit content">
    <h3 class="title">{{title}}</h3>
    <router-link to='/'>Back to imports</router-link>
    <hr>

    <div class="field">
      <label class="label">Enter a description for this import</label>
      <input class="input" type="text" v-bind:disabled="!canEdit" v-model="name" style="max-width: 30em">
    </div>

    <div class="field">
      <label class="label">Data type</label>
      <div class="select">
        <select v-model="dataType">
          <option v-bind:value="1">Type 1</option>
          <option v-bind:value="2">Type 2/3 (Big Data)</option>
        </select>
      </div>
    </div>

    <div class="field">
      <label class="label">Data file</label>
      <p v-if='status == "init"'>
        <button class='button' v-on:click='selectFile'>Select file</button>
      </p>

      <p v-if='uploading'>
        Uploading
        <progress class="progress is-primary is-small" v-bind:value='uploadProgress' max="100">{{uploadProgress}}%</progress>
      </p>

      <p v-if='fileURL && filename && !uploading'>
        File uploaded: <a v-bind:href='fileURL'>{{filename}}</a>
      </p>
    </div>

    <div v-if='processing'>
      <p>
        Processing {{progressString}}
        <progress class="progress is-primary is-small" v-bind:value='processingProgress' max="100">{{processingProgress}}%</progress>
      </p>
    </div>

    <div v-if='status == "checked_ok"' class='notification is-success'>
      👍 Looks good! No errors detected. Please review the log below before importing the data.
    </div>

    <p v-if='status == "checked_ok"'>
      <button class='button is-primary' v-on:click='importData'>Finish importing data</button>
      <button class='button' v-on:click='selectFile'>Upload an edited file</button>
    </p>

    <div v-if='status == "checked_error"' class='notification is-warning'>
      ⚠️ Some issues were detected in the uploaded file. Please check the log below and then upload a new version for checking.
    </div>

    <div v-if='status == "import_error"' class='notification is-warning'>
      ⚠️ Something went wrong while importing data. Please check the log below.
    </div>

    <p v-if='status == "checked_error" || status == "import_error"'>
      <button class='button' v-on:click='selectFile'>Upload an edited file</button>
    </p>

    <div v-if='status == "imported"' class='notification is-success'>
      🎉 All data has been imported without errors. See full import log below.
    </div>

    <div v-if='processingComplete' class="log">
      <h3>Import log</h3>
      <code v-for='log in importLogs' v-bind:class='log.level' style='display: block'>
        {{log.message}}
      </code>
    </div>

    <div v-if='canDelete'>
      <hr>
      <button class='button is-light' v-on:click='deleteImport'>Delete import</button>
    </div>
  </div>

</template>

<script>
import * as api from '@/api'
import * as util from '@/util'

export default {
  name: 'ImportEdit',
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
      return ['checked_ok', 'checked_error', 'imported', 'import_error'].includes(this.status)
    },
    canEdit: function() {
      return ['init', 'checked_ok', 'checked_error', 'import_error'].includes(this.status)
    },
    canProcess: function() {
      return !!(this.name.trim() !== '' && this.fileUUID)
    },
    canDelete: function() {
      return this.importId !== null && this.canEdit
    },
    fileURL: function() {
      if(this.fileUUID) {
        return api.uploadURL(this.fileUUID)
      }
    },
    title: function() {
      return 'NESP Data Import – ' + (this.name || 'Untitled')
    }
  },
  created: function() {
    if(this.$route.params.id !== 'new') {
      this.importId = this.$route.params.id
      this.monitorImport()
    }
  },
  watch: {
    importId: function(val) {
      this.$router.replace('/import/' + val)
    }
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
        name: this.name.trim(),
        data_type: this.dataType
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
@import '~bulma/sass/utilities/initial-variables.sass';
.log { color: #888; }
.error { color: $red; }
.info { color: $blue; }
.warning { color: orange; }

</style>

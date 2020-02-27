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
      <p class="table is-fullwidth is-striped is-hoverable" v-if="imports.length == 0">
        None
      </p>
      <table class="table is-fullwidth is-striped is-hoverable" v-if="imports.length > 0">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in imports">
            <td><a v-bind:href="importUrl(i)">{{i.filename}}</a></td>
            <td>
              {{humanizeStatus(i.status)}}
              <a v-bind:href="importLogUrl(i)">(log)</a>
            </td>
            <td><timeago :since='i.time_created' :auto-update="60"></timeago></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</template>

<script>
import * as api from '@/api'
import Vue from 'vue'
import VueTimeago from 'vue-timeago'
import { humanizeStatus } from '@/util'

Vue.use(VueTimeago, {
  name: 'timeago', // component name, `timeago` by default
  locale: 'en-US',
  locales: {
    // you will need json-loader in webpack 1
    'en-US': require('vue-timeago/locales/en-US.json')
  }
})

export default {
  name: 'ImportList',
  data () {
    var data = {
      imports: [],
      status: 'loading'
    }

    var importsPromise = this.sourceId ? api.dataSourceImports(this.sourceId) : api.dataImports()

    importsPromise.then((imports) => {
      data.imports = imports
        .sort((a, b) => b.time_created.localeCompare(a.time_created))
      data.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      data.status = 'error'
    })

    return data
  },
  methods: {
    importUrl(i) {
      return api.uploadURL(i.upload_uuid)
    },
    importLogUrl(i) {
      return api.dataImportLogUrl(i.id)
    },
    humanizeStatus
  },
  props: {
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .table {
    table-layout: fixed;
  }
  .table th:nth-child(3) {
    width: 8em;
  }
  .table th:nth-child(4) {
    width: 8em;
  }
  .table th:nth-child(5) {
    width: 8em;
  }
  .table tbody tr {
    cursor: pointer;
  }
</style>

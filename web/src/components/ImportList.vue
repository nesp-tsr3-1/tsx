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
            <th style="width: 4em;"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in imports">
            <td :title="i.filename"><span class="tag is-danger" style="margin-right: 0.5em" v-if="i.data_type === 2">Type 2</span><a v-bind:href="importUrl(i)">{{i.filename}}</a>
              <br>
              <span class="tag" v-if="isMostRecentImport(i)">Most recent import – use this file to update your dataset.</span>
            </td>
            <td>
              {{humanizeStatus(i.status)}}
              <a v-bind:href="importLogUrl(i)" target="_blank">(log)</a>
              <button class="button is-small" v-if='canApproveImport(i)' v-on:click='function() { approveImport(i) }' v-bind:class="{ 'is-loading': i.isApproving }">Approve</button>
            </td>
            <td>{{formatDateTime(i.time_created)}} by {{i.user}}</td>
            <td class="visibility">
              <button v-if="canShowImport(i)" @click="showImport(i)" title="Hidden from custodians" :disabled="i.isUpdatingVisibility"><img src="../assets/icons/visibility_off.svg"></button>
              <button v-if="canHideImport(i)" @click="hideImport(i)"  title="Visible to custodians" :disabled="i.isUpdatingVisibility"><img src="../assets/icons/visibility.svg"></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { humanizeStatus, formatDateTime } from '../util.js'

export default {
  name: 'ImportList',
  data () {
    var data = {
      imports: [],
      status: 'loading',
      currentUser: null
    }

    return data
  },
  created () {
    api.currentUser().then(currentUser => {
      this.currentUser = currentUser
    })
    this.refresh()
  },
  methods: {
    refresh() {
      var importsPromise = api.dataSourceImports(this.sourceId)
      importsPromise.then((imports) => {
        imports.forEach(i => {
          i.isApproving = false
          i.isUpdatingVisibility = false
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
    humanizeStatus,
    formatDateTime
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
</style>

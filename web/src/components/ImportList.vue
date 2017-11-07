<template>
  <div class="import-list">
    <p class="table is-fullwidth is-striped is-hoverable" v-if="imports.length == 0">
      None
    </p>
    <table class="table is-fullwidth is-striped is-hoverable" v-if="imports.length > 0">
      <thead>
        <tr>
          <th>Description</th>
          <th>Created</th>
          <th>Status</th>
          <th>Errors</th>
          <th>Warnings</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="i in imports" v-on:click='$router.push("import/" + i.id)'>
          <td>{{i.name}}</td>
          <td><timeago :since='i.created' :auto-update="60"></timeago></td>
          <td>{{humanizeStatus(i.status)}}</td>
          <td>{{i.errors}}</td>
          <td>{{i.warnings}}</td>
        </tr>
      </tbody>
    </table>
  </div>

</template>

<script>
import * as api from '@/api'
import Vue from 'vue'
import VueTimeago from 'vue-timeago'

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
    var data = { imports: [] }

    api.dataImports().then((imports) => {
      console.log(this.completed)
      data.imports = imports.filter(i => (i.status === 'imported') === this.completed)
    })

    return data
  },
  methods: {
    humanizeStatus: function(str) {
      return {
        init: 'Not checked yet',
        checked_ok: 'Checked (OK)',
        checked_error: 'Checked (error)',
        checking: 'Checking',
        importing: 'Importing',
        imported: 'Imported',
        import_error: 'Error during import'
      }[str]
    }
  },
  props: {
    completed: Boolean
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

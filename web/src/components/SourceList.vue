<template>
  <div class="source-list">
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load sources.
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <p class="table is-fullwidth is-striped is-hoverable" v-if="sources.length == 0">
        No datasets to show.
      </p>
      <table class="table is-fullwidth is-striped is-hoverable" v-if="sources.length > 0">
        <thead>
          <tr>
            <th>Description</th>
            <th>Created</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in sources" v-on:click='$router.push("source/" + i.id)'>
            <td :title="i.description">{{truncate(i.description, 40)}}</td>
            <td><timeago :since='i.time_created' :auto-update="60" v-if="i.time_created"></timeago></td>
            <td>{{humanizeStatus(i.status)}}</td>
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
  name: 'sourceList',
  data () {
    var data = {
      sources: [],
      status: 'loading'
    }

    api.dataSources().then((sources) => {
      data.sources = sources
        .sort((a, b) => (b.time_created || '').localeCompare(a.time_created || ''))
      data.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      data.status = 'error'
    })

    return data
  },
  methods: {
    humanizeStatus,
    truncate(str, maxLength) {
      if(str.length > maxLength) {
        var words = str.substr(0, maxLength + 1).split(' ')
        words.pop()
        return words.join(' ') + '…'
      } else {
        return str
      }
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

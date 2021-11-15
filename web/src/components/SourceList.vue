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
      <p v-if="sources.length > 0" class="title is-6">
        Showing {{sources.length}} datasets.
      </p>
      <table class="table is-fullwidth is-striped is-hoverable" v-if="sources.length > 0">
        <thead>
          <tr>
            <th v-on:click="sortBy('description')">Description {{sortIcon('description')}}</th>
            <!-- <th v-on:click="sortBy('monitoring_program')">Program {{sortIcon('monitoring_program')}}</th> -->
            <th v-on:click="sortBy('time_created')">Created {{sortIcon('time_created')}}</th>
            <th v-on:click="sortBy('status')">Status {{sortIcon('status')}}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in sortedSources" v-on:click='$router.push("/source/" + i.id)'>
            <td :title="i.description">{{truncate(i.description, 120)}}</td>
            <!-- <td>{{truncate(i.monitoring_program, 120)}}</td> -->
            <td>{{formatDateTime(i.time_created)}}</td>
            <!-- <td><timeago :since='i.time_created' :auto-update="60" v-if="i.time_created"></timeago></td> -->
            <td>{{humanizeStatus(i.status)}}</td>
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
  name: 'sourceList',
  data () {
    return {
      sources: [],
      status: 'loading',
      sort: {
        key: 'time_created',
        asc: false
      }
    }
  },
  created() {
    api.dataSources().then((sources) => {
      console.log(sources)
      this.sources = sources
      // .sort((a, b) => (b.time_created || '').localeCompare(a.time_created || ''))
      this.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
    humanizeStatus,
    formatDateTime,
    truncate(str, maxLength) {
      if(str.length > maxLength) {
        var words = str.substr(0, maxLength + 1).split(' ')
        words.pop()
        return words.join(' ') + '…'
      } else {
        return str
      }
    },
    sortIcon(key) {
      if(this.sort.key === key) {
        return this.sort.asc ? '▲' : '▼'
      } else {
        return ''
      }
    },
    sortBy(key) {
      if(this.sort.key === key) {
        this.sort.asc = !this.sort.asc
      } else {
        this.sort = {
          key: key,
          asc: true
        }
      }
    }
  },
  computed: {
    sortedSources() {
      let key = this.sort.key
      let result = this.sources.slice().sort((a, b) => (a[key] || '').localeCompare(b[key] || ''))
      if(!this.sort.asc) {
        result.reverse()
      }
      return result
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
  .table th:nth-child(2) {
    width: 12em;
  }
  .table th:nth-child(3) {
    width: 8em;
  }
  .table tbody tr {
    cursor: pointer;
  }
  .table thead th {
    cursor: pointer;
  }
  .table thead th:hover {
    background: #f8f8f8;
  }
</style>

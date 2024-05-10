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
      <div v-if="sources.length > 0" class="columns">
        <p class="column title is-6">Showing {{filteredSources.length}} / {{sources.length}} datasets</p>
        <input class="column input" type="text" placeholder="Search datasets" v-model="searchText">
      </div>
      <table :class="{clickable: clickableRows}" class="table is-fullwidth is-striped is-hoverable" v-if="filteredSources.length > 0">
        <thead>
          <tr>
            <th v-on:click="sortBy('description')">Description {{sortIcon('description')}}</th>
            <th v-on:click="sortBy('time_created')">Created {{sortIcon('time_created')}}</th>
            <th v-if="showModified" v-on:click="sortBy('last_modified')">Modified {{sortIcon('last_modified')}}</th>
            <th v-if="showStatus" v-on:click="sortBy('status')">Status {{sortIcon('status')}}</th>
            <th v-if="actions">Manage</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="source in sortedSources" @click="$emit('clickSource', source)">
            <td :title="source.description">{{truncate(source.description, 120)}}</td>
            <td>{{formatDateTime(source.time_created)}}</td>
            <td v-if="showModified">{{formatDateTime(source.last_modified)}}</td>
            <td v-if="showStatus">{{humanizeStatus(source.status)}}</td>
            <td v-if="actions">
              <button
                class="button is-small is-primary"
                v-for="action in actions"
                @click.stop="$emit('action', action, source)">{{action}}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { humanizeStatus, formatDateTime, debounce } from '../util.js'

function normalize(x) {
  return x.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

export default {
  name: 'SourceList',
  data () {
    return {
      sources: [],
      status: 'loading',
      sort: {
        key: 'time_created',
        asc: false
      },
      searchText: '',
      debouncedSearchText: '',
      showModified: false
    }
  },
  created() {
    this.refresh()
    api.currentUser().then(user => {
      if(user.roles.includes('Administrator')) {
        this.showModified = true
      }
    })
  },
  methods: {
    refresh() {
      let criteria = {}
      if(this.programId) {
        criteria.program_id = this.programId
      }

      api.dataSources(criteria).then((sources) => {
        this.sources = sources
        // .sort((a, b) => (b.time_created || '').localeCompare(a.time_created || ''))
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
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
    filteredSources() {
      let search = normalize(this.debouncedSearchText)
      return search ? this.sources.filter(s => normalize(s.description).indexOf(search) != -1) : this.sources
    },
    sortedSources() {
      let key = this.sort.key
      let result = this.filteredSources.slice().sort((a, b) => (a[key] || '').localeCompare(b[key] || ''))
      if(!this.sort.asc) {
        result.reverse()
      }
      return result
    }
  },
  watch: {
    searchText: debounce(function(searchText) {
      this.debouncedSearchText = searchText
    }, 500)
  },
  props: {
    programId: Number,
    showStatus: {
      type: Boolean,
      default: true
    },
    actions: Array,
    clickableRows: {
      type: Boolean,
      default: true
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .table {
    table-layout: fixed;
  }
  .table th:nth-child(2),
  .table th:nth-child(3) {
    width: 8em;
  }
  .table th:nth-child(4) {
    width: 8em;
  }
  .table.clickable tbody tr {
    cursor: pointer;
  }
  .table thead th {
    cursor: pointer;
  }
  .table thead th:hover {
    background: #f8f8f8;
  }
</style>

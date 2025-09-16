<template>
  <!-- Note: this functionality not in use (see email 15 Jun 2022) -->
  <div class="program-list">
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load programs.
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <p
        v-if="programs.length == 0"
        class="table is-fullwidth is-striped is-hoverable"
      >
        No programs to show.
      </p>
      <div
        v-if="programs.length > 0"
        class="columns"
      >
        <p class="column title is-6">
          Showing {{ filteredPrograms.length }} / {{ programs.length }} programs
        </p>
        <input
          v-model="searchText"
          class="column input"
          type="text"
          placeholder="Search programs"
        >
      </div>
      <table
        v-if="filteredPrograms.length > 0"
        class="table is-fullwidth is-striped is-hoverable"
      >
        <thead>
          <tr>
            <th @click="sortBy('description')">
              Program {{ sortIcon('description') }}
            </th>
            <th @click="sortBy('source_count')">
              Datasets {{ sortIcon('source_count') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="i in sortedPrograms"
            :key="i.id"
            @click="$router.push('/program/' + i.id)"
          >
            <td :title="i.description">
              {{ i.description }}
            </td>
            <td>{{ i.source_count.toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { formatDateTime, debounce } from '../util.js'

function normalize(x) {
  return x.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

function compare(a, b) {
  if(typeof a === "string") {
    return a.localeCompare(b)
  } else {
    return (a > b) ? 1 : (a < b) ? -1 : 0
  }
}

export default {
  name: 'ProgramList',
  props: {
    completed: Boolean
  },
  data () {
    return {
      programs: [],
      status: 'loading',
      sort: {
        key: 'description',
        asc: false
      },
      searchText: '',
      debouncedSearchText: ''
    }
  },
  computed: {
    filteredPrograms() {
      let search = normalize(this.debouncedSearchText)
      return search ? this.programs.filter(s => normalize(s.description).indexOf(search) != -1) : this.programs
    },
    sortedPrograms() {
      let key = this.sort.key
      let result = this.filteredPrograms.slice().sort((a, b) => compare(a[key], b[key]))
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
  created() {
    api.monitoringPrograms().then((programs) => {
      this.programs = programs
      this.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
    formatDateTime,
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

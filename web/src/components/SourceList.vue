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
            <th @click="sortBy('description')"
              class="col-description">
              Description {{sortIcon('description')}}
            </th>
            <th @click="sortBy('time_created')"
              class="col-time-created">
              Created {{sortIcon('time_created')}}
            </th>
            <th v-if="showModified"
              @click="sortBy('last_modified')"
              class="col-last-modified">
              Modified {{sortIcon('last_modified')}}
            </th>
            <th v-if="showStatus"
              @click="sortBy('status')"
              class="col-status">
              Status {{sortIcon('status')}}
            </th>
            <th v-if="showAgreement"
              @click="sortBy('data_agreement_status_description')"
              class="col-agreement-status">
              Agreement {{sortIcon('data_agreement_status_description')}}
            </th>
            <th v-if="actions"
              class="col-actions">
              Manage
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="source in sortedSources" @click="$emit('clickSource', source, $event)">
            <td :title="source.description">
              <template v-for="[nonMatch, match] in source.descriptionParts">
                <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                <b style="white-space: pre-wrap;">{{match}}</b>
              </template>
              <div>
                <span v-for="parts in source.custodianParts" class="tag is-info is-light">
                  <template v-for="[nonMatch, match] in parts">
                    <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                    <b style="white-space: pre-wrap;">{{match}}</b>
                  </template>
                </span>
              </div>
            </td>
            <td>{{formatDateTime(source.time_created)}}</td>
            <td v-if="showModified">{{formatDateTime(source.last_modified)}}</td>
            <td v-if="showStatus">{{humanizeStatus(source.status)}}</td>
            <td v-if="actions">
              <button
                class="button is-small is-primary"
                v-for="action in actions"
                @click.stop="$emit('action', action, source)">{{action}}</button>
            </td>
            <td v-if="showAgreement">{{source.data_agreement_status_description}}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { humanizeStatus, formatDateTime, debounce, searchStringToRegex, matchParts } from '../util.js'

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
      showModified: false,
      navigationsSinceBackButtonPressed: 2
    }
  },
  created() {
    this.refresh()
    api.currentUser().then(user => {
      if(user.roles.includes('Administrator')) {
        this.showModified = true
      }
    })

    // Work-around for detecting back button so we can preserve search/scroll state (see activated hook)
    // TODO: make this a global solution if it works well
    // e.g. util.installBackButtonDetection(this.$router) in app startup, then $router.lastNavigationWasBack elsewhere
    this.$router.options.history.listen((to, from, info) => {
      this.navigationsSinceBackButtonPressed = 0
    })
    this.$router.beforeEach((to, from) => {
      this.navigationsSinceBackButtonPressed++
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
      let search = this.debouncedSearchText

      if(search) {
        let searchRegex = searchStringToRegex(search)

        function filterSource(s) {
          return s.description.match(searchRegex) || (s.custodians && s.custodians.some(c => c.match(searchRegex)))
        }

        let matchingSources = this.sources.filter(filterSource)
        for(let source of matchingSources) {
          source.descriptionParts = matchParts(source.description, searchRegex)
          source.custodianParts = (source.custodians || [])
            .map(custodian => matchParts(custodian, searchRegex))
            .filter(parts => parts.length > 1)
        }
        return matchingSources
      } else {

        for(let source of this.sources) {
          source.descriptionParts = [[source.description, ""]]
          source.custodianParts = []
        }
        return this.sources
      }
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
    showAgreement: {
      type: Boolean,
      default: false
    },
    actions: Array,
    clickableRows: {
      type: Boolean,
      default: true
    }
  },
  emits: ["clickSource"],
  activated() {
    // We use KeepAlive to preserve state when returning to the datasets page via the back button,
    // but unfortunately this also preserves state even when navigating to the datasets page via
    // the navigation bar.
    // The work-around below resets the page state if we are *not* arriving at this page via the back button
    let lastNavigationWasBack = (this.navigationsSinceBackButtonPressed == 1)
    if(!lastNavigationWasBack) {
      this.debouncedSearchText = this.searchText = ''
      this.refresh()
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .table {
    table-layout: fixed;
  }
  .table th.col-status,
  .table th.col-time-created,
  .table th.col-last-modified,
  .table th.col-actions {
    width: 8em;
  }
  .table th.col-agreement-status {
    width: 14em;
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

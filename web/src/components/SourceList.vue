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
      <p
        v-if="sources.length == 0"
        class="table is-fullwidth is-striped is-hoverable"
      >
        No datasets to show.
      </p>
      <template v-if="sources.length > 0">
        <div class="columns is-align-items-center">
          <div class="column is-6 has-text-weight-bold">
            Showing {{ filteredSources.length }} / {{ sources.length }} datasets
          </div>
          <div class="column is-6">
            <input
              v-model="searchText"
              class="input"
              type="text"
              placeholder="Search datasets"
            >
          </div>
        </div>
        <div
          v-if="showAgreement"
          class="is-flex is-justify-content-end is-align-items-center"
          style="margin-bottom: 1em;"
        >
          <div class="select is-rounded">
            <select v-model="dataAgreementStatusFilter">
              <option :value="null">
                Any agreement status
              </option>
              <template
                v-for="option in dataAgreementStatusOptions"
                :key="option.code"
              >
                <option :value="option.code">
                  {{ option.description }}
                </option>
              </template>
            </select>
          </div>
        </div>
      </template>
      <table
        v-if="filteredSources.length > 0"
        :class="{clickable: clickableRows}"
        class="table is-fullwidth is-striped is-hoverable"
      >
        <thead>
          <tr>
            <th
              class="col-description"
              @click="sortBy('description')"
            >
              Description {{ sortIcon('description') }}
            </th>
            <th
              class="col-time-created"
              @click="sortBy('time_created')"
            >
              Created {{ sortIcon('time_created') }}
            </th>
            <th
              v-if="showModified"
              class="col-last-modified"
              @click="sortBy('last_modified')"
            >
              Modified {{ sortIcon('last_modified') }}
            </th>
            <th
              v-if="showStatus"
              class="col-status"
              @click="sortBy('status')"
            >
              Status {{ sortIcon('status') }}
            </th>
            <th
              v-if="showAgreement"
              class="col-agreement-status"
              @click="sortBy('data_agreement_status_description')"
            >
              Agreement {{ sortIcon('data_agreement_status_description') }}
            </th>
            <th
              v-if="actions"
              class="col-actions"
            >
              Manage
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="source in sortedSources"
            :key="source.id"
            @click="$emit('clickSource', source, $event)"
          >
            <td :title="source.description">
              <template
                v-for="([nonMatch, match], index) in source.descriptionParts"
                :key="index"
              >
                <span style="white-space: pre-wrap;">{{ nonMatch }}</span>
                <b style="white-space: pre-wrap;">{{ match }}</b>
              </template>
              <div>
                <span
                  v-for="(parts, partsIndex) in source.custodianParts"
                  :key="partsIndex"
                  class="tag is-info is-light"
                >
                  <template
                    v-for="([nonMatch, match], index) in parts"
                    :key="index"
                  >
                    <span style="white-space: pre-wrap;">{{ nonMatch }}</span>
                    <b style="white-space: pre-wrap;">{{ match }}</b>
                  </template>
                </span>
              </div>
              <!-- eslint-enable -->
            </td>
            <td>{{ formatDateTime(source.time_created) }}</td>
            <td v-if="showModified">
              {{ formatDateTime(source.last_modified) }}
            </td>
            <td v-if="showStatus">
              {{ humanizeStatus(source.status) }}
            </td>
            <td v-if="actions">
              <button
                v-for="action in actions"
                :key="action"
                class="button is-small is-primary"
                @click.stop="$emit('action', action, source)"
              >
                {{ action }}
              </button>
            </td>
            <td v-if="showAgreement">
              {{ source.data_agreement_status_description }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { humanizeStatus, formatDateTime, debounce, searchStringToRegex, matchParts } from '../util.js'

export default {
  name: 'SourceList',
  props: {
    programId: {
      type: Number,
      default: undefined
    },
    showStatus: {
      type: Boolean,
      default: true
    },
    showAgreement: {
      type: Boolean,
      default: false
    },
    actions: {
      type: Array,
      default: undefined
    },
    clickableRows: {
      type: Boolean,
      default: true
    }
  },
  emits: ['clickSource', 'action'],
  data() {
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
      navigationsSinceBackButtonPressed: 2,
      dataAgreementStatusOptions: null,
      dataAgreementStatusFilter: null
    }
  },
  computed: {
    filteredSources() {
      let matchingSources = this.sources
      let search = this.debouncedSearchText

      if(search) {
        let searchRegex = searchStringToRegex(search)

        function filterSource(s) {
          return s.description.match(searchRegex) || (s.custodians && s.custodians.some(c => c.match(searchRegex)))
        }

        matchingSources = matchingSources.filter(filterSource)
        for(let source of matchingSources) {
          source.descriptionParts = matchParts(source.description, searchRegex)
          source.custodianParts = (source.custodians || [])
            .map(custodian => matchParts(custodian, searchRegex))
            .filter(parts => parts.length > 1)
        }
      } else {
        for(let source of matchingSources) {
          source.descriptionParts = [[source.description, '']]
          source.custodianParts = []
        }
      }

      let agreementStatus = this.dataAgreementStatusFilter
      if(agreementStatus) {
        matchingSources = matchingSources.filter(s =>
          s.data_agreement_status == agreementStatus)
      }

      return matchingSources
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
  created() {
    this.refresh()
    api.currentUser().then((user) => {
      if(user.roles.includes('Administrator')) {
        this.showModified = true
      }
    })
    api.dataAgreementStatusOptions().then((x) => {
      this.dataAgreementStatusOptions = x
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

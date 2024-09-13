<template>
  <div class="section">
    <div class="container feedback-home">
      <div class="columns">
        <div class="column is-12 is-offset-0">
          <user-nav></user-nav>
          <h2 class="title">Custodian Feedback Forms</h2>

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

          <div v-if="status === 'loaded'">

            <div v-if="taxonDatasets.length > 0" class="columns">
              <p class="column title is-6">Showing {{filteredTaxonDatasets.length}} / {{taxonDatasets.length}} taxon datasets</p>
              <input class="column input" type="text" placeholder="Search taxon datasets" v-model="searchText">
            </div>

            <table class='table is-fullwidth is-striped is-hoverable clickable' v-if="filteredTaxonDatasets.length > 0">
              <thead>
                <tr>
                  <th v-on:click="sortBy('description')">
                    Taxon Dataset {{sortIcon('description')}}
                  </th>
                  <th v-on:click="sortBy('time_created')">
                    Latest form created {{sortIcon('time_created')}}
                  </th>
                  <th v-on:click="sortBy('last_modified')">
                    Latest form modified {{sortIcon('last_modified')}}
                  </th>
                  <th v-on:click="sortBy('integrated_feedback_status')">
                    Latest form status {{sortIcon('integrated_feedback_status')}}
                  </th>
                  <th v-if="isAdmin" v-on:click="sortBy('admin_feedback_status')">
                    Admin status {{sortIcon('admin_feedback_status')}}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="taxonDataset in sortedTaxonDatasets" @click="handleDatasetClick(taxonDataset, $event)">
                  <td>
                    <span class='tag'>{{taxonDataset.id}}</span>
                    <span v-if="!taxonDataset.data_present" class='tag is-warning' title='Taxon not present in latest data import'>Taxon Dataset removed</span>
                    <p>
                      <template v-for="[nonMatch, match] in taxonDataset.descriptionParts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </p>
                    <p>
                      <template v-for="[nonMatch, match] in taxonDataset.taxonParts">
                        <span style="white-space: pre-wrap;">{{nonMatch}}</span>
                        <b style="white-space: pre-wrap;">{{match}}</b>
                      </template>
                    </p>
                  </td>
                  <td>{{formatDateTime(taxonDataset.time_created)}}</td>
                  <td>{{formatDateTime(taxonDataset.last_modified)}}</td>
                  <td>{{taxonDataset.integrated_feedback_status.description}}</td>
                  <td v-if="isAdmin">{{taxonDataset.admin_feedback_status?.description}}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { handleLinkClick, formatDateTime, debounce, searchStringToRegex, matchParts } from '../util.js'

let sortMappings = {
  description(ds) {
    return ds.source.description
  },
  last_modified(ds) {
    return ds.last_modified
  },
  time_created(ds) {
    return ds.time_created
  },
  integrated_feedback_status(ds) {
    return ds.integrated_feedback_status.description
  },
  admin_feedback_status(ds) {
    return ds.admin_feedback_status.description
  },
}

export default {
  name: 'CustodianFeedbackHome',
  data () {
    return {
      currentUser: null,
      status: 'loading',
      taxonDatasets: [],
      searchText: '',
      debouncedSearchText: '',
      sort: {
        key: 'time_created',
        asc: false
      }
    }
  },
  created() {
    this.refresh()
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })

    api.currentUser().then(currentUser => {
      this.currentUser = currentUser
    }).catch(error => {
      this.error = error
    })
  },
  computed: {
    filteredTaxonDatasets() {
      let search = this.debouncedSearchText
      console.log(search)
      if(search) {
        let searchRegex = searchStringToRegex(search)

        function filterDataset(ds) {
          return ds.source.description.match(searchRegex) ||
            ds.taxon.scientific_name.match(searchRegex)
        }

        let matchingDatasets = this.taxonDatasets.filter(filterDataset)
        for(let dataset of matchingDatasets) {
          dataset.descriptionParts = matchParts(dataset.source.description, searchRegex)
          dataset.taxonParts = matchParts(dataset.taxon.scientific_name, searchRegex)
        }

        return matchingDatasets
      } else {
        for(let dataset of this.taxonDatasets) {
          dataset.descriptionParts = [[dataset.source.description, ""]]
          dataset.taxonParts = [[dataset.taxon.scientific_name, ""]]
        }
        return this.taxonDatasets
      }
    },
    sortedTaxonDatasets() {
      let key = this.sort.key
      let mapping = sortMappings[key]
      let result = this.filteredTaxonDatasets.slice().sort((a, b) => (mapping(a) || '').localeCompare(mapping(b) || ''))
      if(!this.sort.asc) {
        result.reverse()
      }
      return result
    },
    isAdmin() {
      return this.currentUser?.is_admin
    }
  },
  watch: {
    searchText: debounce(function(searchText) {
      console.log(searchText)
      this.debouncedSearchText = searchText
    }, 500)
  },
  methods: {
    refresh() {
      api.taxonDatasets().then((taxonDatasets) => {
        this.taxonDatasets = taxonDatasets
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    handleDatasetClick(taxonDataset, evt) {
      let url = "/custodian_feedback/" + taxonDataset.id
      handleLinkClick(evt, url, this.$router)
    },
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
  /*.table {
    table-layout: fixed;
  }
  .table th:nth-child(2),
  .table th:nth-child(3) {
    width: 8em;
  }
  .table th:nth-child(4) {
    width: 8em;
  }*/
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

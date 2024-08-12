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
            <table class='table is-fullwidth is-striped is-hoverable clickable' v-if="filteredTaxonDatasets.length > 0">
              <thead>
                <tr>
                  <th>Taxon Dataset</th>
                  <th>Latest form created</th>
                  <th>Latest form modified</th>
                  <th>Latest form status</th>
                  <th>Admin status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="taxonDataset in filteredTaxonDatasets" @click="handleDatasetClick(taxonDataset, $event)">
                  <td>
                    <span class='tag'>{{taxonDataset.id}}</span>
                    <p>{{taxonDataset.source.description}}</p>
                    <p>{{taxonDataset.taxon.scientific_name}}</p>
                  </td>
                  <td>{{formatDateTime(taxonDataset.time_created)}}</td>
                  <td>{{formatDateTime(taxonDataset.last_modified)}}</td>
                  <td>{{taxonDataset.integrated_feedback_status.description}}</td>
                  <td>{{taxonDataset.admin_feedback_status?.description}}</td>
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
import { handleLinkClick, formatDateTime } from '../util.js'

export default {
  name: 'CustodianFeedbackHome',
  data () {
    return {
      currentUser: null,
      status: 'loading',
      taxonDatasets: []
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
      return this.taxonDatasets.filter(() => true)
    }
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
    formatDateTime
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

<template>
  <div class="section">
    <div class="container feedback-home">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <div v-if="status == 'loading'">
            <p>
              Loading…
            </p>
          </div>
          <div v-if="status == 'error'">
            <p>
              Failed to load feedback forms.
            </p>
          </div>

          <div v-if="status === 'loaded'">
            <h2 class="title">{{taxonDataset.taxon.scientific_name}}</h2>
            <p class="content">
              <span class="tag is-large">{{taxonDataset.id}}</span>
            </p>
            <hr>

            <p class="content">
              The forms below are based on your dataset
              <router-link :to="{ name: 'SourceView', params: { id: taxonDataset.source.id }}">{{taxonDataset.source.description}}</router-link></p>

            <h3 class="title">Form History</h3>

            <table class='table is-fullwidth is-striped is-hoverable' v-if="taxonDataset.forms.length > 0">
              <thead>
                <tr>
                  <th>Form</th>
                  <th></th>
                  <th>Created</th>
                  <th>Modified</th>
                  <th>Status</th>
                  <th>Type</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="form in taxonDataset.forms">
                  <td>
                    {{taxonDataset.taxon.scientific_name}}
                    <span class='tag'>{{taxonDataset.id}}</span>
                  </td>
                  <td>
                    <router-link :to="{ name: 'CustodianFeedbackForm', params: { id: form.id }}" tag="button" class="button is-dark is-small" v-if="canEdit(form)">{{editButtonLabel(form)}}</router-link>
                  </td>
                  <td>{{formatDateTime(form.time_created)}}</td>
                  <td>{{formatDateTime(form.last_modified)}}</td>
                  <td>{{form.feedback_status.description}}</td>
                  <td>{{form.feedback_type.description}}</td>
                  <td>
                    <div class='button is-small' @click="downloadForm(form)">Download (pdf)</div>
                  </td>
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
  name: 'CustodianFeedbackDataset',
  data () {
    return {
      currentUser: null,
      status: 'loading',
      taxonDatasetId: this.$route.params.id,
      taxonDataset: null,
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
  },
  methods: {
    refresh() {
      api.taxonDataset(this.taxonDatasetId).then((taxonDataset) => {
        this.taxonDataset = taxonDataset
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    formatDateTime,
    canEdit(form) {
      return ['incomplete', 'draft', 'complete'].includes(form.feedback_status.code)
    },
    editButtonLabel(form) {
      return form.feedback_status.code == 'incomplete' ? 'Start' : 'Edit'
    },
    downloadForm(form) {
      alert('Not yet implemented - under development')
    },
    // handleFormClick(form, evt) {
    //   let url = "/custodian_feedback/form/" + form.id
    //   handleLinkClick(evt, url, this.$router)
    // },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

<template>
  <div class="section">
    <div class="container feedback-home">
      <div class="columns">
        <div class="column is-12 is-offset-0">
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
            <p v-if="!taxonDataset.data_present" class="notification is-warning">
              The most recent data import for this dataset does not contain any records with this taxon.
            </p>

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
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="form in taxonDataset.forms">
                  <td>
                    {{taxonDataset.taxon.scientific_name}}
                    <span class='tag'>{{taxonDataset.id}}</span>
                  </td>
                  <td>
                    <div class="buttons">
                      <router-link v-if="canEdit(form)"
                        :to="{ name: 'EditCustodianFeedbackForm', params: { id: form.id }}" tag="button" class="button is-dark is-small" >{{editButtonLabel(form)}}</router-link>
                      <router-link v-if="canView(form)"
                        :to="{ name: 'ViewCustodianFeedbackForm', params: { id: form.id }}" tag="button" class="button is-dark is-small" >View</router-link>
                    </div>
                  </td>
                  <td>{{formatDateTime(form.time_created)}}</td>
                  <td>{{formatDateTime(form.last_modified)}}</td>
                  <td>{{form.feedback_status.description}}</td>
                  <td>{{form.feedback_type.description}}</td>
                  <td>
                    <a class="button is-small" target="_blank" v-if="downloadURL(form)" :href="downloadURL(form)">{{downloadLabel(form)}}</a>
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
      taxonDataset: null
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
  watch: {

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
    canView(form) {
      return form.feedback_type.code == 'integrated' && form.is_current_form_version
    },
    editButtonLabel(form) {
      return form.feedback_status.code == 'incomplete' ? 'Start' : 'Edit'
    },
    downloadForm(form) {
      alert('Not yet implemented - under development')
    },
    downloadURL(form) {
      if(form.feedback_type.code == 'integrated') {
        return api.custodianFeedbackFormPDFURL(form.id)
      } else if(form.feedback_type.code == 'spreadsheet') {
        return api.custodianFeedbackFormDownloadURL(form.id)
      } else if(form.feedback_type.code == 'admin') {
        return api.custodianFeedbackFormCSVURL(form.id)
      }
    },
    downloadLabel(form) {
      if(form.feedback_type.code == 'admin') {
        return 'Download (CSV)'
      } else if(form.feedback_type.code == 'integrated') {
        return 'Download (PDF)'
      } else if(form.feedback_type.code == 'spreadsheet') {
        return 'Download (XLSX)'
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

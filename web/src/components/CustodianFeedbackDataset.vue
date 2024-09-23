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
                    <template v-if="canEdit(form)">
                      <button v-if="consentRequired && !consentGiven"
                        @click="promptConsent" class="button is-dark is-small">{{editButtonLabel(form)}}</button>
                      <router-link v-else
                        :to="{ name: 'CustodianFeedbackForm', params: { id: form.id }}" tag="button" class="button is-dark is-small" >{{editButtonLabel(form)}}</router-link>
                    </template>
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

            <hr>

            <!-- Conditions and Consent -->
            <div v-if="consentRequired">
              <div class="content" id="consent_section">
                <h3>Conditions and consent</h3>
                <p>
                  These feedback forms are based on the species monitoring data generously donated by you or your organisation as a data custodian for the development of Australia's Threatened Species Index. The index will allow for integrated reporting at national, state and regional levels, and track changes in threatened species populations. The goal of this feedback process is to inform decisions about which datasets will be included in the overall multi-species index. If custodians deem datasets to be unrepresentative of true species trends, these may be excluded from final analyses.
                </p>
                <p>
                  Within your individual datasets (see the ‘Datasets’ tab) you can access a clean version of your processed data in a (1) raw (confidential) and (2) aggregated format (to be made open to the public unless embargoed). For your aggregated data, please note that site names will be masked and spatial information on site locations will be denatured to the IBRA subregion centroids before making the data available to the public. We use the 'Living Planet Index' method to calculate trends (Collen et. 2009) and follow their requirements on data when we assess suitability of data for trends.
                </p>
                <p>
                  The information we collect from you using these forms is part of an elicitation process for the project “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species”. We would like to inform you of the following:
                </p>
                <ul>
                  <li>
                    Data collected will be anonymous and you will not be identified by name in any publication arising from this work without your consent.
                  </li>
                  <li>
                    All participation in this process is voluntary. If at any time you do not feel comfortable providing information, you have the right to withdraw any or all of your input to the project.
                  </li>
                  <li>
                    Data collected from this study will be used to inform the Threatened Species Index at national and various regional scales.
                  </li>
                  <li>
                    Project outputs will include a web tool and a publicly available aggregated dataset that enables the public to interrogate trends in Australia’s threatened species over space and time.
                  </li>
                </ul>
                <p>
                  This study adheres to the Guidelines of the ethical review process of The University of Queensland and the National Statement on Ethical Conduct in Human Research. Whilst you are free to discuss your participation in this study with project staff (Project Manager Tayla Lawrie: <a href='mailto:t.lawrie@uq.edu.au'>t.lawrie@uq.edu.au</a> or <b>0476 378 354</b>), if you would like to speak to an officer of the University not involved in the study, you may contact the Ethics Coordinator on 07 3443 1656.
                </p>
                <p>
                  Your involvement in this elicitation process constitutes your consent for the Threatened Species Index team to use the information collected in research, subject to the information provided above.
                </p>
                <p>
                  <b>References</b><br>
                  Collen, B., J. Loh, S. Whitmee, L. McRae, R. Amin, and J. E. Baillie. 2009. Monitoring change in vertebrate abundance: the living planet index. Conserv Biol 23:317-327.
                </p>
                <p>
                  <b>I have read and understand the conditions of the expert elicitation study for the project, “A threatened species index for Australia: Development and interpretation of integrated reporting on trends in Australia's threatened species” and provide my consent.</b>
                </p>
              </div>
              <div>
                <div class="field">
                  <label class="checkbox required">
                    <input type="checkbox" v-model="localConsent.consent_given" />
                    I agree
                  </label>
                </div>
                <div class="field">
                  <label class="label required">Please enter your name.</label>
                  <div class="control">
                    <input class="input" type="text" placeholder="" v-model="localConsent.consent_name">
                  </div>
                </div>
                <div class="field">
                  <div class="control">
                    <button class="button is-primary" :disabled="!canSaveConsent" @click="saveConsent">Save</button>
                  </div>
                </div>
                <p class="help is-danger" v-if="showConsentPrompt">Please complete and save the consent form above in order to access the custodian feedback form.</p>
                <p class="help is-success" v-if="consentState == 'saved'">Consent form saved.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import * as api from '../api.js'
import { handleLinkClick, formatDateTime, deepEquals } from '../util.js'

export default {
  name: 'CustodianFeedbackDataset',
  data () {
    return {
      currentUser: null,
      status: 'loading',
      taxonDatasetId: this.$route.params.id,
      taxonDataset: null,
      remoteConsent: {},
      localConsent: {},
      showConsentPromptIfNecessary: false,
      consentState: 'idle'
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
    consentRequired() {
      return !this.currentUser?.is_admin
    },
    consentGiven() {
      return this.remoteConsent?.consent_given
    },
    canSaveConsent() {
      return !deepEquals(this.localConsent, this.remoteConsent) && !(this.localConsent.consent_given && !this.localConsent.consent_name)
    },
    showConsentPrompt() {
      return this.showConsentPromptIfNecessary && !this.consentGiven
    }
  },
  watch: {
    canSaveConsent(canSave) {
      if(canSave && this.consentState == 'saved') {
        this.consentState = 'idle'
      }
    }
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
      api.custodianFeedbackConsent().then((data) => {
        this.localConsent = { ...data }
        this.remoteConsent = { ...data }
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
    saveConsent() {
      this.consentState = 'saving'
      api.updateCustodianFeedbackConsent(this.localConsent).then(() => {
          this.consentState = 'saved'
          this.remoteConsent = { ... this.localConsent }
      }).catch((error) => {
        console.log(error)
        this.consentState = 'error'
      })
    },
    promptConsent() {
      this.showConsentPromptIfNecessary = true
      document.getElementById("consent_section")?.scrollIntoView(true)
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

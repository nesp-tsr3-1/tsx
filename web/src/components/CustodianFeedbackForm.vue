<template>
  <div class="section">
    <div class="container feedback-home">
      <div class="columns">
<!-- <aside class="menu" v-if="status == 'loaded'">
    <ul class="menu-list">
      <li><a>Data citation and monitoring aims</a></li>
      <li><a>Data summary and processing</a></li>
      <li><a>Statistics and trend estimate</a></li>
      <li><a>Data suitability</a></li>
      <li><a>Funding, logistics and governance (optional)</a></li>
    </ul>
  </aside> -->
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <div v-if="status == 'loading'">
            <p>
              Loading…
            </p>
          </div>
          <div v-if="status == 'error'">
            <p>
              Failed to load form.
            </p>
          </div>

          <div v-if="status === 'loaded'">

            <!-- <div style="white-space: pre;">{{formJSON}}</div> -->

            <div class="columns">
              <div class="column">
                <h2 class="title">{{form.taxon.scientific_name}}</h2>
                <p class="content">
                  <span class="tag is-large">{{form.dataset_id}}</span>
                </p>
              </div>
              <div class="column is-narrow">
                <div class="buttons">
                  <button class="button is-primary" :disabled="!canSaveDraft" @click="saveAndClose">{{saveButtonLabel}}</button>
                  <button class="button is-primary" :disabled="!canSubmit">Submit</button>
                </div>
                <p class="help is-danger" v-if="saveStatus == 'error'">Failed to save form</p>
              </div>
            </div>

            <hr>

            <!---- Conditions and consent ---->

            <div v-if="notAdmin">
              <div class="content">
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
                  This study adheres to the Guidelines of the ethical review process of The University of Queensland and the National Statement on Ethical Conduct in Human Research. Whilst you are free to discuss your participation in this study with project staff (Project Coordinator Tayla Lawrie: <a href='mailto:t.lawrie@uq.edu.au'>t.lawrie@uq.edu.au</a> or <b>0476 378 354</b>), if you would like to speak to an officer of the University not involved in the study, you may contact the Ethics Coordinator on 07 3443 1656.
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
              <div class="indent">
                <div class="field">
                  <label class="checkbox required">
                    <input type="checkbox" v-model="formData.consent_given" />
                    I agree
                  </label>
                </div>
                <div class="field">
                  <label class="label required">Please enter your name.</label>
                  <div class="control">
                    <input class="input" type="text" placeholder="" v-model="formData.consent_name">
                  </div>
                </div>
              </div>
              <hr>
            </div>

            <!---- Data citation and monitoring aims ---->

            <div class="content">
              <h3>Data citation and monitoring aims</h3>
              <p>
                <b>Data citation</b><br>
                {{citation}}
              </p>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you agree with the above suggested citation for your data? If no, please indicate how to correctly cite your data.</label>
              <label class="label required" v-if="isAdmin">Does the custodian agree with the suggested citation? If no, what changes have they suggested to correctly cite their data?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="citation_ok" v-model="formData.citation_ok" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="citation_ok" v-model="formData.citation_ok" value="no" /> No
                  </label>
                </div>
                <input class="input" type="text" placeholder="Suggested citation" v-if="formData.citation_ok == 'no'" v-model="formData.citation_suggestion">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Has your monitoring program been explicitly designed to detect population trends over time? If no / unsure, please indicate the aims of your monitoring.</label>
              <label class="label required" v-if="isAdmin">Is the monitoring program explicitly designed to detect population trends over time? If no or unsure, what are the aims of their monitoring?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="no" /> No
                  </label>
                  <label class="radio">
                    <input type="radio" name="designed_for_trends" v-model="formData.designed_for_trends" value="unsure" /> Unsure
                  </label>
                </div>
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.designed_for_trends_comments" v-if="formData.designed_for_trends === 'no' || formData.designed_for_trends === 'unsure'">
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Do you analyse your own data for trends?</label>
              <label class="label required" v-if="isAdmin">Does the custodian analyse their own data for trends?</label>
              <div class="control indent">
                <div class="radio-list">
                  <label class="radio">
                    <input type="radio" name="analysed_for_trends" v-model="formData.analysed_for_trends" value="yes" /> Yes
                  </label>
                  <label class="radio">
                    <input type="radio" name="analysed_for_trends" v-model="formData.analysed_for_trends" value="no" /> No
                  </label>
                </div>
              </div>
            </div>

            <div class="field numbered">
              <label class="label required" v-if="notAdmin">Can you estimate what percentage (%) of your species’ population existed in Australia at the start of your monitoring (assuming this was 100% in 1750)? <strong>This information is to help understand population baselines and determine whether the majority of a species' decline may have occurred prior to monitoring.</strong></label>
              <label class="label required" v-if="isAdmin">What has the custodian estimated to be the percentage (%) of the species’ population that existed in Australia at the start of the monitoring (assuming this was 100% in 1750)?</label>
              <div class="control indent">
                <input class="input" type="text" placeholder="Enter your answer" v-model="formData.estimated_population_baseline_percentage">
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
import { handleLinkClick, formatDateTime } from '../util.js'
import { generateCitation } from '../util.js'

export default {
  name: 'CustodianFeedbackForm',
  data () {
    return {
      currentUser: null,
      status: 'loading',
      saveStatus: 'none',
      formId: this.$route.params.id,
      form: null,
      formData: {

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
    showConsent() {
      return true
    },
    citation() {
      let source = this.form.source
      return source && generateCitation(source.authors, source.details, source.provider)
    },
    isAdmin() {
      return this.form.feedback_type.code === 'admin'
    },
    notAdmin() {
      return this.form.feedback_type.code !== 'admin'
    },
    formJSON() {
      return JSON.stringify(this.formData, null, 4);
    },
    saveButtonLabel() {
      if(this.saveStatus == 'saving') {
        return 'Saving…'
      } else {
        return 'Save Draft'
      }
    },
    canSaveDraft() {
      return this.saveStatus != 'saving'
    },
    canSubmit() {
      // TODO
      return false
    }
  },
  methods: {
    refresh() {
      api.custodianFeedbackForm(this.formId).then((form) => {
        this.form = form
        this.formData = { ... form.answers }
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    formatDateTime,
    save(close) {
      let json = { ... this.formData }
      this.saveStatus = 'saving'
      setTimeout(() => {
        api.updateCustodianForm(this.formId, json).then(() => {
          this.saveStatus = 'saved'
        }).catch((error) => {
          console.log(error)
          this.saveStatus = 'error'
        }).then(() => {
          if(this.saveStatus == 'saved' && close) {
            this.$router.push({ name: 'CustodianFeedbackDataset', params: { id: this.form.dataset_id }})
          }
        })
      }, 1000)
    },
    saveAndClose() {
      this.save(true)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .indent {
    padding-left: 2em;
  }

  .label {
/*    font-weight: normal;*/
  }

  label.required::after {
    content: "*";
    color: red;
  }

  aside.menu {
    position: sticky;
    display: inline-block;
    vertical-align: top;
    max-height: 100vh;
    overflow-y: auto;
    width: 200px;
    top: 0;
    bottom: 0;
    padding: 30px;
  }

  .radio-list label.radio {
    display: block;
    margin-left: 0;
    margin-bottom: 0.5em;
  }

  .field {
    margin-bottom: 2em;
  }

  section {
    counter-reset: question-counter;
  }
  .field.numbered {
    counter-increment: question-counter;
  }
  .field.numbered > label {
    text-indent: 2em hanging;
  }
  .field.numbered > label:before {
    width: 2em;
    display: inline-block;
    content: counter(question-counter) ". ";
  }
</style>

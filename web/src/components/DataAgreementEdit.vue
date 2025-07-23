<template>
  <div class="section">
    <div>
      <div class="columns">
        <div class="column is-offset-2 is-8">
          <user-nav></user-nav>
        </div>
      </div>
      <div class="columns">
        <div class="column is-2 menu-border-right">
          <div class="sticky-top">
            <p class="menu-label">Contents</p>
            <ul class="menu-list" ref="sideMenu">
              <li>
                <a href="#upload_section">Upload document</a>
              </li>
              <li>
                <a href="#conditions_section">Conditions to data sharing</a>
              </li>
              <li>
                <a href="#provider_section">Data provider details</a>
              </li>
              <li>
                <a href="#data_section">Provided data description</a>
              </li>
              <li>
                <a href="#signatory_section">Signatory details</a>
              </li>
            </ul>
          </div>
        </div>


        <div class="column is-8">
          <h2 class="title is-3">{{ title }}</h2>
          <div class="content" v-if="lastEditDescription">
            {{lastEditDescription}}
          </div>
          <form>
            <fieldset v-if="loaded" v-bind:disabled="submitting">
              <h3 class="title is-5" id="upload_section">Upload document</h3>

              <!-- Uploaded files -->
              <div class="content" v-if="uploadedFiles.length > 0">
                <table class="table" style="width: 100%">
                  <thead>
                    <tr>
                      <th>Uploaded files</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="file in uploadedFiles">
                      <td>
                        <a v-bind:href='file.downloadURL()'>{{file.filename}}</a>
                      </td>
                      <td style="width: 10em; text-align: right;">
                        <button type="button" class="button is-small is-dark" @click="() => file.remove()">Remove file</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Uploading files -->
              <div class="content" v-if="uploadingFiles.length > 0">
                <table class="table" style="width: 100%">
                  <thead>
                    <tr>
                      <th>Uploads in progress</th>
                      <th></th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="file in uploadingFiles">
                      <td>
                        {{file.filename}}<br>
                        <progress v-if="file.state == 'uploading'" class="progress is-primary is-small" v-bind:value='file.uploadProgress' max="100">{{file.uploadProgress}}%</progress>
                      </td>
                      <td>
                        <p v-if='file.state == "error"' class="content has-text-danger">Upload failed</p>
                        <p v-if='file.state == "uploading"' class="content">Uploading</p>
                      </td>
                      <td style="width: 10em; text-align: right;">
                        <button v-if='file.state == "error"'
                          type="button"
                          class="button is-small is-light"
                          @click="() => file.remove()">
                          Clear
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <p class="content">
                <button type="button" class="button" @click="selectFile">Select file(s)…</button>
              </p>

              <p class="help is-danger" v-if="errors.files">{{ errors.files }}</p>

              <h3 class="title is-5" id="conditions_section">Conditions to data sharing</h3>

              <div class="field">
                <label class="label required">1. Does the data provider permit data sharing with ALA?</label>
                <div class="control">
                  <div class="horizontal-radio-list">
                    <label><input class="radio" type="radio" name="agreement.ala_yes" v-model="agreement.ala_yes" :value="true" /> Yes</label>
                    <label><input class="radio" type="radio" name="agreement.ala_yes" v-model="agreement.ala_yes" :value="false" /> No</label>
                  </div>
                </div>
                <p class="help is-danger" v-if="errors.ala_yes">{{ errors.ala_yes }}</p>
              </div>


              <div class="field">
                <label class="label required">2. Does the data provider permit data sharing with DCCEEW?</label>
                <div class="control">
                  <div class="horizontal-radio-list">
                    <label><input class="radio" type="radio" name="agreement.dcceew_yes" v-model="agreement.dcceew_yes" :value="true" /> Yes</label>
                    <label><input class="radio" type="radio" name="agreement.dcceew_yes" v-model="agreement.dcceew_yes" :value="false" /> No</label>
                  </div>
                </div>
                <p class="help is-danger" v-if="errors.dcceew_yes">{{ errors.dcceew_yes }}</p>
              </div>

              <div class="field">
                <label class="label required">3. Please enter below the details of any additional conditions regarding <strong>raw data</strong> handling listed by the data provider.</label>
                <input class="input" type="text" v-model="agreement.conditions_raw">
                <p class="help is-danger" v-if="errors.conditions_raw">{{ errors.conditions_raw }}</p>
              </div>

              <div class="field">
                <label class="label required">4. Please enter below the details of any additional conditions regarding <strong>sensitive data</strong> handling listed by the data provider.</label>
                <input class="input" type="text" v-model="agreement.conditions_sensitive">
                <p class="help is-danger" v-if="errors.conditions_sensitive">{{ errors.conditions_sensitive }}</p>
              </div>

              <div class="field">
                <label class="label">5. Has the data provider included an expiry date for the agreement?</label>
                <div class="control">
                  <div class="horizontal-radio-list">
                    <label><input class="radio" type="radio" name="agreement.has_expiry_date" v-model="agreement.has_expiry_date" :value="true" /> Yes</label>
                    <label><input class="radio" type="radio" name="agreement.has_expiry_date" v-model="agreement.has_expiry_date" :value="false" /> No</label>
                  </div>
                </div>
                <div class="control" v-if="agreement.has_expiry_date">
                  <input class="input" type="date" v-model="agreement.expiry_date">
                  <p class="help is-danger" v-if="errors.expiry_date">{{ errors.expiry_date }}</p>
                </div>
              </div>

              <div class="field">
                <label class="label">6. Has the data provider included an embargo period on the publication of the aggregated de-identified data?</label>
                <div class="control">
                  <div class="horizontal-radio-list">
                    <label><input class="radio" type="radio" name="agreement.has_embargo_date" v-model="agreement.has_embargo_date" :value="true" /> Yes</label>
                    <label><input class="radio" type="radio" name="agreement.has_embargo_date" v-model="agreement.has_embargo_date" :value="false" /> No</label>
                  </div>
                </div>
                <div class="control" v-if="agreement.has_embargo_date">
                  <input class="input" type="date" v-model="agreement.embargo_date">
                  <p class="help is-danger" v-if="errors.embargo_date">{{ errors.embargo_date }}</p>
                </div>
              </div>

              <h3 class="title is-5" id="provider_section">Data provider details</h3>

              <div class="field">
                <label class="label">7. What are the organisational details of the data provider as listed in Schedule A?</label>
                <input class="input" type="text" v-model="agreement.provider_organisation">
                <p class="help is-danger" v-if="errors.provider_organisation">{{ errors.provider_organisation }}</p>
              </div>

              <div class="field">
                <label class="label">8. What is the name of the data provider as listed in Schedule A?</label>
                <input class="input" type="text" v-model="agreement.provider_name">
                <p class="help is-danger" v-if="errors.provider_name">{{ errors.provider_name }}</p>
              </div>

              <div class="field">
                <label class="label">9. What are the position details of the data provider as listed in Schedule A?</label>
                <input class="input" type="text" v-model="agreement.provider_position">
                <p class="help is-danger" v-if="errors.provider_position">{{ errors.provider_position }}</p>
              </div>

              <div class="field">
                <label class="label">10. What are the contact details of the data provider as listed in Schedule A?</label>
              </div>

              <div class="field is-horizontal">
                <div class="field-label is-normal">
                  <label class="label">Email address</label>
                </div>
                <div class="field-body">
                  <div class="control">
                    <input class="input" type="text" v-model="agreement.provider_email" />
                  </div>
                </div>
                <p class="help is-danger" v-if="errors.provider_email">{{ errors.provider_email }}</p>
              </div>

              <div class="field is-horizontal">
                <div class="field-label is-normal">
                  <label class="label">Phone number</label>
                </div>
                <div class="field-body">
                  <div class="control">
                    <input class="input" type="text" v-model="agreement.provider_phone" />
                  </div>
                </div>
                <p class="help is-danger" v-if="errors.provider_phone">{{ errors.provider_phone }}</p>
              </div>

              <div class="field">
                <label class="label">11. What is the postal address details for the data provider as listed in Schedule A?</label>
                <input class="input" type="text" v-model="agreement.provider_postal_address">
                <p class="help is-danger" v-if="errors.provider_postal_address">{{ errors.provider_postal_address }}</p>
              </div>

              <div class="field">
                <label class="label">12. What is the ABN for the data provider as listed in Schedule A?</label>
                <input class="input" type="text" v-model="agreement.provider_abn">
                <p class="help is-danger" v-if="errors.provider_abn">{{ errors.provider_abn }}</p>
              </div>

              <h3 class="title is-5" id="data_section">Provided data description</h3>

              <div class="field">
                <label class="label">13. What is the description of the provided data as listed in Schedule A? </label>
                <input class="input" type="text" v-model="agreement.data_description">
                <p class="help is-danger" v-if="errors.data_description">{{ errors.data_description }}</p>
              </div>

              <h3 class="title is-5" id="signatory_section">Signatory details</h3>

              <h4 class="title is-6">The University of Queensland</h4>

              <div class="field">
                <label class="label">14. What date was the agreement signed by the UQ authorised signatory? </label>
                <input class="input" type="date" v-model="agreement.uq_date_signed">
                <p class="help is-danger" v-if="errors.uq_date_signed">{{ errors.uq_date_signed }}</p>
              </div>

              <div class="field">
                <label class="label">15. What is the name of the UQ authorised signatory?</label>
                <input class="input" type="text" v-model="agreement.uq_signatory">
                <p class="help is-danger" v-if="errors.uq_signatory">{{ errors.uq_signatory }}</p>
              </div>

              <div class="field">
                <label class="label">16. What is the name of the witness to the UQ authorised signatory?</label>
                <input class="input" type="text" v-model="agreement.uq_witness">
                <p class="help is-danger" v-if="errors.uq_witness">{{ errors.uq_witness }}</p>
              </div>

              <h4 class="title is-6">Data Provider</h4>

              <div class="field">
                <label class="label">17. What date was the agreement signed by the authorised signatory for the data provider?</label>
                <input class="input" type="date" v-model="agreement.provider_date_signed">
                <p class="help is-danger" v-if="errors.provider_date_signed">{{ errors.provider_date_signed }}</p>
              </div>

              <div class="field">
                <label class="label">18. What is the name of the authorised signatory for the data provider?</label>
                <input class="input" type="text" v-model="agreement.provider_signatory">
                <p class="help is-danger" v-if="errors.provider_signatory">{{ errors.provider_signatory }}</p>
              </div>

              <div class="field">
                <label class="label">19. What is the name of the witness to the authorised signatory for the data provider?</label>
                <input class="input" type="text" v-model="agreement.provider_witness">
                <p class="help is-danger" v-if="errors.provider_witness">{{ errors.provider_witness }}</p>
              </div>

              <hr>

              <div class="is-flex is-flex-direction-row is-justify-content-space-between">
                <div class="buttons">
                  <button
                    type="button"
                    class="button is-primary"
                    v-if="agreement.is_draft"
                    @click="saveAndClose">Save Draft and Close
                  </button>
                  <button
                    type="button"
                    class="button is-primary"
                    @click='submit'>{{ buttonLabel }}</button>
                </div>
                <div class="buttons">
                  <button
                    type="button"
                    class="button is-danger is-light"
                    v-if="canDelete"
                    @click="deleteAgreement">Delete Agreement
                  </button>
                </div>
              </div>
              <p class="help is-danger" v-if="submitError">{{submitError}}</p>
            </fieldset>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { selectFiles, pick, setupPageNavigationHighlighting } from '../util.js'
import { reactive } from 'vue'

function withFullStop(str) {
  return str.trim().replace(/\.?$/, ".")
}


export default {
  name: 'DataAgreementEdit',
  data () {
    var dataAgreementId = this.$route.params.id
    return {
      isNew: dataAgreementId === 'new',
      dataAgreementId: (dataAgreementId === 'new') ? undefined : dataAgreementId,
      submitting: false,
      errors: {},
      submitError: null,
      agreement: undefined,
      loaded: false,
      files: []
    }
  },
  computed: {
    title() {
      return this.isNew ? 'New Agreement Details' : 'Edit Agreement Details'
    },
    buttonLabel() {
      return this.isNew ? 'Create Agreement' : 'Update Agreement'
    },
    fileURL() {
      if(this.agreement.upload_uuid) {
        return api.uploadURL(this.agreement.upload_uuid)
      }
    },
    lastEditDescription() {
      if(this.agreement?.last_edited && this.agreement?.last_edited_by) {
        let lastEdited = new Date(Date.parse(this.agreement?.last_edited))
        return "Last modified by " +
          this.agreement?.last_edited_by + " on " +
          lastEdited.toLocaleDateString()
      } else {
        return null
      }
    },
    uploadedFiles() {
      return this.files.filter(f => f.state == 'uploaded')
    },
    uploadingFiles() {
      return this.files.filter(f => f.state != 'uploaded')
    },
    canDelete() {
      return !this.isNew && this.agreement?.source_ids.length == 0
    }
  },
  created() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    if(this.dataAgreementId) {
      api.dataAgreement(this.dataAgreementId).then((agreement) => {
        this.agreement = agreement
        this.files = agreement.files.map(f => this.fileModelFromJSON(f))
        this.uploadState = this.agreement.upload_uuid ? 'uploaded' : 'no_upload'
        this.loaded = true
      })
    } else {
      this.agreement = {
        is_draft: true
      }
      this.uploadState = 'no_upload'
      this.loaded = true
    }
  },
  mounted() {
    this.navHighlighter = setupPageNavigationHighlighting(this.$refs.sideMenu)
  },
  unmounted() {
    this.navHighlighter?.dispose()
  },
  methods: {
    submit() {
      this.save(false)
    },
    deleteAgreement() {
      if(window.confirm("Are you sure you wish to delete this agreement?")) {
        this.submitError = null;
        api.deleteDataAgreement(this.dataAgreementId).then(() => {
          this.$router.push({ path: '/documents/data_agreements' })
        }).catch(error => {
          this.submitError = "Failed to delete agreement"
        })
      }
    },
    saveAndClose() {
      this.agreement.is_draft = true
      this.save(true)
    },
    save(asDraft) {
      var agreement = JSON.parse(JSON.stringify(this.agreement))
      agreement.is_draft = asDraft
      agreement.files = this.files.map(f => f.toJSON()).filter(x => x)

      this.submitError = null
      this.submitting = true
      setTimeout(function() {
        this.submitting = false
      }, 1000)

      var promise
      if(this.isNew) {
        promise = api.createDataAgreement(agreement)
      } else {
        agreement.id = this.dataAgreementId
        promise = api.updateDataAgreement(agreement.id, agreement)
      }

      promise.then(agreement => {
        this.$router.push({ path: '/documents/data_agreements' })
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
          this.submitError = "Unable to update data agreement due to invalid or missing details. Review the fields above for further information."
        } else {
          this.errors = { 'server_error': true }
          this.submitError = "Something went wrong while processing your request."
        }
      }).finally(() => {
        this.submitting = false
      })
    },
    selectFile() {
      selectFiles({
        accept: 'application/pdf',
        multiple: true
      }).then((files) => {
        // Clear any existing error files before uploading
        this.files = this.files.filter(f => f.state != 'error');

        for(let file of files) {
          let fileModel = this.fileModelFromFile(file);
          fileModel.upload()
          this.files.push(fileModel)
        }
      })
    },
    fileModelFromFile(file) {
      return this.fileModel(file)
    },
    fileModelFromJSON(json) {
      return this.fileModel(undefined, json)
    },
    fileModel(file, json) {
      let parent = this

      let fileModel
      if(file) {
        fileModel = reactive({
          state: 'uploading',
          uploadProgress: 0,
          uploadUUID: null,
          filename: file.name,
          upload() {
            if(file) {
              api.upload(file, (progress) => {
                this.uploadProgress = progress * 100
              }).then((result) => {
                this.uploadUUID = result.uuid
                this.state = 'uploaded'
              }).catch((e) => {
                console.log(e)
                this.state = 'error'
              })
            }
          }
        })
      } else {
        fileModel = reactive({
          state: 'uploaded',
          uploadProgress: 100,
          uploadUUID: json.upload_uuid,
          filename: json.filename,
          upload() {
          }
        })
      }

      fileModel.remove = function() {
        parent.files = parent.files.filter(x => x !== this)
      }

      fileModel.downloadURL = function() {
        if(this.uploadUUID) {
          return api.uploadURL(this.uploadUUID)
        }
      }

      fileModel.toJSON = function() {
        if(this.state == 'uploaded') {
          return {
            filename: this.filename,
            upload_uuid: this.uploadUUID
          }
        }
      }

      return fileModel
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

.sticky-top {
  position: sticky;
  top: 1em;
}

.menu-list a.current {
  font-weight: bold;
}

.menu-border-right {
  border-right: 0.5px solid #eee;
}

label.required::after {
  content: "*";
  color: red;
}

.horizontal-radio-list label {
  margin-right: 0.5em;
}

.horizontal-radio-list {
  margin-bottom: 0.5em;
}

.title.is-6 {
  font-weight: normal;
  font-style: italic;
}

.title.is-5 {
  margin-top: 3em;
  border-bottom: 2px solid #eee;
  padding-bottom: 1em;
}

.field {
  margin-bottom: 2em;
}

</style>

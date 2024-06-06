<template>
  <div class="section">
    <div class="container is-widescreen">
      <div class="columns">
        <div class="column is-offset-2 is-8">
          <user-nav></user-nav>
        </div>
      </div>
      <div class="columns">
        <div class="column is-offset-2 is-8">
          <h2 class="title is-3">{{ title }}</h2>
          <form>
            <fieldset v-bind:disabled="submitting">
              <div class="field">
                <label class="label">Dataset description</label>
                <div class="control">
                  <input class="input" type="text" name="description" v-model="description" autofocus>
                </div>
                <p class="help is-danger" v-if="errors.description">{{ errors.description }}</p>
                <p class="help">Provide a description of the dataset, as per the 'SourceDesc' field in the TSX data import template. The format should be: 'State/Territory-Species/Taxon Group(s)-Institution/Organisation’. Example: "SA-Acacia_araneosa-DEW".</p>
              </div>
              <div class="field">
                <label class="label">Data details</label>
                <div class="control">
                  <input class="input" type="text" name="details" v-model="details">
                </div>
                <p class="help">Provide further details on the dataset, as per the 'SourceDescDetails' field in the TSX data import template. If relevant, please include information on who compiled the data. Example: "Balcanoona Wattle annual monitoring. Compiled by Jane Doe."</p>
                <p class="help is-danger" v-if="errors.details">{{ errors.details }}</p>
              </div>
              <div class="field">
                <label class="label">Data provider</label>
                <div class="control">
                  <input class="input" type="text" name="provider" v-model="provider">
                </div>
                <p class="help">Specify the institution, organisation, or individual who has provided the dataset, as per the 'SourceProvider' field in the TSX data import template. Example: "SA Department of Environment and Water".</p>
                <p class="help is-danger" v-if="errors.provider">{{ errors.provider }}</p>
              </div>
              <div class="field">
                <label class="label">Author(s)</label>
                <div class="control">
                  <input class="input" type="text" name="authors" v-model="authors">
                </div>
                <p class="help">List the authors of the dataset. Example: "SA Government" or "Doe, J".</p>
                <p class="help is-danger" v-if="errors.authors">{{ errors.authors }}</p>
              </div>
              <div class="field">
                <label class="label">Data citation</label>
                <p class="textarea">{{citation}}</p>
                <p class="help">This field is auto-generated based on the above information. To adjust the citation, modify the relevant details and select ‘Update Dataset’.</p>
              </div>
              <div class="field">
                <label class="label">Monitoring program</label>
                <div class="control">
                  <div class="select">
                    <select v-model="monitoring_program">
                      <option v-bind:value="null" selected>N/A</option>
                      <option v-for="mp in monitoringPrograms" v-bind:value="mp">{{ mp }}</option>
                      <option v-bind:value="'__new__'">New program…</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="field"  v-if="monitoring_program === '__new__'">
                <div class="control">
                  <input class="input" type="text" name="monitoring_program" v-model="new_monitoring_program" placeholder="Name of monitoring program">
                </div>
                <p class="help is-danger" v-if="errors.monitoring_program">{{ errors.monitoring_program }}</p>
              </div>

              <h3 class="title is-4" style="margin-top: 1em">Contact</h3>
              <div class="field">
                <label class="label">Full name</label>
                <div class="control">
                  <input class="input" type="text" name="contact_name" v-model="contact_name" placeholder="e.g. Joe Bloggs">
                </div>
                <p class="help is-danger" v-if="errors.contact_name">{{ errors.contact_name }}</p>
              </div>
              <div class="field">
                <label class="label">Institution</label>
                <div class="control">
                  <input class="input" type="text" name="contact_institution" v-model="contact_institution">
                </div>
                <p class="help is-danger" v-if="errors.contact_institution">{{ errors.contact_institution }}</p>
              </div>
              <div class="field">
                <label class="label">Position</label>
                <div class="control">
                  <input class="input" type="text" name="contact_position" v-model="contact_position">
                </div>
                <p class="help is-danger" v-if="errors.contact_position">{{ errors.contact_position }}</p>
              </div>
              <div class="field">
                <label class="label">Email</label>
                <div class="control">
                  <input class="input" type="text" name="contact_email" v-model="contact_email" placeholder="e.g. user@example.com">
                </div>
                <p class="help is-danger" v-if="errors.contact_email">{{ errors.contact_email }}</p>
              </div>
              <div class="field">
                <label class="label">Phone number</label>
                <div class="control">
                  <input class="input" type="text" name="contact_phone" v-model="contact_phone" placeholder="e.g. (01) 2345 6789, 0412 345 678">
                </div>
                <p class="help is-danger" v-if="errors.contact_phone">{{ errors.contact_phone }}</p>
              </div>
              <button type="button" class="button is-primary" v-on:click='submit' style="margin: 0.5em 0;">{{ buttonLabel }}</button>
            </fieldset>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import _ from 'underscore'
import { generateCitation } from '../util.js'

const sourceProps = ['description', 'details', 'provider', 'authors', 'monitoring_program', 'contact_name', 'contact_institution', 'contact_position', 'contact_email', 'contact_phone']

function withFullStop(str) {
  return str.trim().replace(/\.?$/, ".")
}

export default {
  name: 'SourceEdit',
  data () {
    var sourceId = this.$route.params.id
    return {
      isNew: sourceId === 'new',
      sourceId: (sourceId === 'new') ? undefined : sourceId,
      monitoringPrograms: [],
      submitting: false,
      errors: {},
      description: '',
      details: '',
      provider: '',
      authors: '',
      monitoring_program: null,
      new_monitoring_program: '',
      contact_name: '',
      contact_institution: '',
      contact_position: '',
      contact_email: '',
      contact_phone: ''
    }
  },
  computed: {
    title: function() {
      return this.isNew ? 'New Dataset' : 'Edit Dataset Details'
    },
    buttonLabel: function() {
      return this.isNew ? 'Create Dataset' : 'Update Dataset'
    },
    citation: function() {
      return generateCitation(this.authors, this.details, this.provider)
    }
  },
  created() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    if(this.sourceId) {
      api.dataSource(this.sourceId).then((source) => {
        for(let k of sourceProps) {
          this[k] = source[k]
        }
      })
    }
    api.monitoringPrograms().then((mps) => {
      this.monitoringPrograms = mps.map(mp => mp.description)
    })
  },
  methods: {
    submit: function() {
      var source = _.pick(this, sourceProps)

      if(source.monitoring_program === '__new__') {
        source.monitoring_program = this.new_monitoring_program
      }

      this.submitting = true

      var promise
      if(this.isNew) {
        promise = api.createDataSource(source)
      } else {
        source.id = this.sourceId
        promise = api.updateDataSource(source)
      }

      promise.then(source => {
        this.$router.push({ path: '/datasets/' + source.id })
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
        } else {
          this.errors = { 'server_error': true }
        }
      }).finally(() => {
        this.submitting = false
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.source-edit {
  font-size: 100%;
  width: 100%;
  max-width: 40em;
  margin: 0 auto;
}
fieldset {
  border: none;
}
fieldset:disabled {
  opacity: 0.7;
}
</style>

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
                <label class="label">Program name</label>
                <div class="control">
                  <input class="input" type="text" name="description" v-model="description" autofocus>
                </div>
                <p class="help is-danger" v-if="errors.description">{{ errors.description }}</p>
              </div>
              <div class="field">
                <label class="label">Program summary</label>
                <div class="control">
                  <textarea class="textarea" name="summary" v-model="summary"></textarea>
                </div>
                <p class="help is-danger" v-if="errors.summary">{{ errors.summary }}</p>
              </div>
              <div class="field">
                <label class="label">Program lead</label>
                <div class="control">
                  <input class="input" type="text" name="lead" v-model="lead">
                </div>
                <p class="help is-danger" v-if="errors.lead">{{ errors.lead }}</p>
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
import { pick } from '../util.js'

const programProps = ['description', 'summary', 'lead']

export default {
  name: 'ProgramEdit',
  data () {
    var programId = this.$route.params.id
    return {
      isNew: programId === 'new',
      programId: (programId === 'new') ? undefined : programId,
      submitting: false,
      errors: {},
      description: '',
      summary: '',
      lead: ''
    }
  },
  computed: {
    title: function() {
      return this.isNew ? 'New Program' : 'Edit Program Details'
    },
    buttonLabel: function() {
      return this.isNew ? 'Create Program' : 'Update Program'
    }
  },
  created() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    if(this.programId) {
      api.monitoringProgram(this.programId).then((program) => {
        for(let k of programProps) {
          this[k] = program[k]
        }
      })
    }
  },
  methods: {
    submit: function() {
      var program = pick(this, programProps)

      this.submitting = true

      var promise
      if(this.isNew) {
        promise = api.createMonitoringProgram(program)
      } else {
        program.id = this.programId
        promise = api.updateMonitoringProgram(program)
      }

      promise.then(program => {
        this.$router.push({ path: '/program/' + program.id })
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
textarea {
  width:  100%;
  resize:  vertical;
  min-height:  10em;
}
fieldset {
  border: none;
}
fieldset:disabled {
  opacity: 0.7;
}
</style>

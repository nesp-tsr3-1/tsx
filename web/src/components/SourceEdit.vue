<template>
  <div class="section">
    <div class="container is-widescreen">
      <div class="columns">
        <div class="column is-offset-2 is-8">
          <user-nav></user-nav>
        </div>
      </div>
      <div class="columns">
        <div class="column is-offset-2 is-4">
          <h2 class="title is-3">{{ title }}</h2>
          <form>
            <fieldset v-bind:disabled="submitting">
              <div class="field">
                <label class="label">Dataset description</label>
                <div class="control">
                  <input class="input" type="text" name="description" v-model="description" autofocus>
                </div>
                <p class="help is-danger" v-if="errors.description">{{ errors.description }}</p>
              </div>
              <div class="field">
                <label class="label">Data provider</label>
                <div class="control">
                  <input class="input" type="text" name="provider" v-model="provider">
                </div>
                <p class="help is-danger" v-if="errors.provider">{{ errors.provider }}</p>
              </div>
              <div class="field">
                <label class="label">Author(s)</label>
                <div class="control">
                  <input class="input" type="text" name="authors" v-model="authors">
                </div>
                <p class="help is-danger" v-if="errors.authors">{{ errors.authors }}</p>
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
import * as api from '@/api'
import SourceList from '@/components/SourceList'
import _ from 'underscore'

const sourceProps = ['description', 'provider', 'authors', 'contact_name', 'contact_position', 'contact_email', 'contact_phone']

export default {
  name: 'ImportHome',
  components: {
    'source-list': SourceList
  },
  data () {
    var sourceId = this.$route.params.id
    return {
      isNew: sourceId === 'new',
      sourceId: (sourceId === 'new') ? undefined : sourceId,
      submitting: false,
      errors: {},
      description: '',
      provider: '',
      authors: '',
      contact_name: '',
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
  },
  methods: {
    submit: function() {
      var source = _.pick(this, sourceProps)

      this.submitting = true

      var promise
      if(this.isNew) {
        promise = api.createDataSource(source)
      } else {
        source.id = this.sourceId
        promise = api.updateDataSource(source)
      }

      promise.then(source => {
        this.$router.push({ path: '/source/' + source.id })
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

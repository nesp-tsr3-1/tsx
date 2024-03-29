<template>
  <div>
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load custodians.
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <div class="columns is-multiline">
        <user-row v-for="user in users"
          v-bind:key="user.id"
          v-bind:user="user"
          v-bind:sourceId="sourceId"
          @deleted="refresh">
          <div class="column is-half">
            <div class="card">
              <div class="card-content">
                <button class="delete" @click="deleteUser" style="position: absolute; top: 1.5rem; right: 1rem;"></button>
                <div>
                  <span style="font-weight: bold">{{displayName}}</span>
                </div>
                <div>
                  <a v-bind:href="'mailto: ' + user.email">{{user.email}}</a>
                </div>
                <div v-if="!isRegistered" class="is-size-7">
                  This user has not signed up for an account yet
                </div>
                <div class="spinner" v-if="state == 'updating' || state == 'deleting'">
                  One moment…
                </div>
              </div>
            </div>
          </div>
        </user-row>
      </div>
      <p v-if="users.length === 0" class="content">
        This dataset currently has no custodians.
      </p>

      <fieldset>
        <div class="field has-addons">
          <div class="control">
            <input class="input" style="width: 15em" type="text"
              placeholder="Custodian email address"
              v-model="newCustodianEmail"
              @focus="newCustodianEmailFocused = true"
              @blur="newCustodianEmailFocused = false"
              v-on:keyup.enter="addUser">
          </div>
          <div class="control">
            <button class="button is-info" :disabled="!enableSubmit" @click="addUser">Add Custodian</button>
          </div>
        </div>
        <p v-if="submitStatus === 'error' && submitErrorMessage" class="help is-danger">{{submitErrorMessage}}</p>
      </fieldset>

    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import SourceCustodian from './SourceCustodian.vue'

export default {
  name: 'SourceCustodians',
  components: {
    'user-row': SourceCustodian
  },
  data () {
    return {
      users: [],
      status: 'loading',
      submitStatus: 'init',
      submitErrorMessage: null,
      newCustodianEmail: '',
      newCustodianEmailFocused: false
    }
  },
  computed: {
    enableSubmit: function() {
      return this.newCustodianEmail.trim().length > 0
    },
    showSubmit: function() {
      return this.enableSubmit || this.newCustodianEmailFocused
    }
  },
  created() {
    this.refresh()
  },
  methods: {
    refresh() {
      this.status = 'loading'
      api.dataSourceCustodians(this.sourceId).then((users) => {
        this.users = users
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    addUser() {
      if(this.newCustodianEmail.trim() === '') {
        return
      }
      this.submitStatus = 'submitting'
      api.addDataSourceCustodian(this.sourceId, this.newCustodianEmail.trim()).then(() => {
        this.newCustodianEmail = ''
        this.refresh()
        this.submitStatus = 'init'
      }).catch((error) => {
        this.submitErrorMessage = (error.json && error.json.error) || 'Something went wrong'
        this.submitStatus = 'error'
      })
    }
  },
  props: {
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

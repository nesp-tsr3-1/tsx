<template>
  <!-- Note: this functionality not in use (see email 15 Jun 2022) -->
  <div class="content">
    <p>Program managers are users who can view and download the raw, time-series and trend data for all datasets associated with this program.</p>

    <p v-if="status == 'loading'">
      Loading…
    </p>

    <p v-if="status == 'error'">
      Failed to load program managers.
    </p>

    <div v-if="status == 'loaded'">
      <div class="columns is-multiline">
        <div
          v-for="manager in managers"
          :key="manager.id"
          class="column is-half"
        >
          <div class="card">
            <div class="card-content">
              <button
                v-if="canEdit"
                class="delete"
                style="position: absolute; top: 1.5rem; right: 1rem;"
                @click="deleteManager(manager)"
              />
              <div v-if="manager.first_name">
                <span style="font-weight: bold">{{ manager.first_name + ' ' + manager.last_name }}</span>
              </div>
              <div style="overflow: hidden; text-overflow: ellipsis;">
                <a
                  :href="'mailto: ' + manager.email"
                  :title="manager.email"
                >{{ manager.email }}</a>
              </div>
              <div
                v-if="!manager.first_name"
                class="is-size-7"
              >
                This user has not signed up for an account yet
              </div>
            </div>
          </div>
        </div>
      </div>
      <p
        v-if="managers.length === 0"
        class="content"
        style="font-weight: bold;"
      >
        This program currently has no managers.
      </p>
      <p
        v-if="!canEdit"
        style="font-style: italic;"
      >
        Please contact a member of the Threatened Species Index team at <a href="mailto:tsx@uq.edu.au">tsx@uq.edu.au</a> if you wish to add or remove a program manager for this program.
      </p>

      <fieldset v-if="canEdit">
        <div class="field has-addons">
          <div class="control">
            <input
              v-model="newManagerEmail"
              class="input"
              style="width: 15em"
              type="text"
              placeholder="Program manager email address"
              @keyup.enter="addManager"
            >
          </div>
          <div class="control">
            <button
              class="button is-info"
              :disabled="!enableSubmit"
              @click="addManager"
            >
              Add Manager
            </button>
          </div>
        </div>
        <p
          v-if="submitStatus === 'error' && submitErrorMessage"
          class="help is-danger"
        >
          {{ submitErrorMessage }}
        </p>
      </fieldset>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'ProgramManagers',
  props: {
    programId: {
      type: Number,
      required: true
    },
    canEdit: Boolean
  },
  data() {
    return {
      managers: [],
      status: 'loading',
      submitStatus: 'init',
      submitErrorMessage: null,
      newManagerEmail: '',
      newManagerEmailFocused: false
    }
  },
  computed: {
    enableSubmit: function() {
      return this.newManagerEmail.trim().length > 0
    },
    showSubmit: function() {
      return this.enableSubmit || this.newManagerEmailFocused
    }
  },
  created() {
    this.refresh()
  },
  methods: {
    refresh() {
      this.status = 'loading'
      api.programManagers(this.programId).then((managers) => {
        this.managers = managers
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    addManager() {
      if(this.newManagerEmail.trim() === '') {
        return
      }
      this.submitStatus = 'submitting'
      api.addManagerToMonitoringProgram(this.programId, this.newManagerEmail.trim()).then(() => {
        this.newManagerEmail = ''
        this.refresh()
        this.submitStatus = 'init'
      }).catch((error) => {
        this.submitErrorMessage = (error.json && error.json.error) || 'Something went wrong'
        this.submitStatus = 'error'
      })
    },
    deleteManager(manager) {
      if(window.confirm('Are you sure you wish to remove this program manager?')) {
        api.removeManagerFromMonitoringProgram(this.programId, manager.id).then(() => {
          this.refresh()
        }).catch((error) => {
          console.log(error)
          alert('Failed to remove program manager')
        })
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

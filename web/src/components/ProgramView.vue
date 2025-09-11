<template>
  <div class="section">
    <div
      v-if="program"
      class="container is-widescreen program-view"
    >
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav />

          <h2 class="title">
            {{ program.description }}
          </h2>

          <hr>

          <h4 class="title is-4">
            Program Details
            <router-link
              :to="{ name: 'ProgramEdit', params: { id: programId }}"
              tag="button"
              class="button is-small"
            >
              Edit
            </router-link>
          </h4>

          <div class="columns">
            <div class="column">
              <div style="margin-bottom: 1em;">
                <div style="font-weight: bold;">
                  Program Summary
                </div>
                {{ program.summary || 'N/A' }}
              </div>

              <div style="margin-bottom: 1em;">
                <div style="font-weight: bold;">
                  Program Lead
                </div>
                {{ program.lead || 'N/A' }}
              </div>
            </div>
          </div>

          <h4 class="title is-4">
            Program Managers
          </h4>
          <program-managers
            :program-id="programId"
            :can-edit="canManageManagers"
          />

          <div>
            <h4 class="title is-4">
              Datasets
            </h4>
            <source-list
              ref="sourceList"
              :clickable-rows="false"
              :show-status="false"
              :program-id="programId"
              :actions="['Remove']"
              @action="handleSourceAction"
            />
          </div>

          <div v-if="deletePermitted">
            <hr>

            <h4 class="title is-6">
              Delete Program
            </h4>
            <p class="content">
              Deleting this program will remove it from the index and cannot be undone. This will reset the monitoring program to 'N/A' for all associated datasets.
            </p>
            <div class="field">
              <input
                id="checkbox"
                v-model="enableDelete"
                type="checkbox"
              >
              <label for="checkbox"> I understand and wish to delete this program</label>
            </div>
            <button
              class="button is-danger"
              :disabled="!enableDelete"
              @click="deleteProgram"
            >
              Delete this program
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="sourceToRemove"
      class="modal is-active"
    >
      <div class="modal-background" />
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">
            Remove dataset
          </p>
        </header>
        <section class="modal-card-body">
          <h5 class="title is-5">
            {{ sourceToRemove.description }}
          </h5>
          <p>Removing this dataset from the monitoring program will set it's monitoring program to "N/A". The dataset will not be removed from the database.</p>
        </section>
        <footer class="modal-card-foot">
          <button
            class="button is-success"
            @click.once="removeSource"
          >
            Remove dataset
          </button>
          <button
            class="button"
            @click="sourceToRemove = null"
          >
            Cancel
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'
import SourceList from './SourceList.vue'
import ProgramManagers from './ProgramManagers.vue'
import { plotTrend } from '../plotTrend'

export default {
  name: 'ProgramView',
  components: {
    'spinner': Spinner,
    'source-list': SourceList,
    'program-managers': ProgramManagers
  },
  data () {
    return {
      programId: +this.$route.params.id,
      program: null,
      enableDelete: false,
      sourceToRemove: null,
      managerStatus: "loading",
      managers: []
    }
  },
  computed: {
    deletePermitted() {
      return this.program && this.program.can_delete
    },
    canManageManagers() {
      return this.program && this.program.can_manage_managers
    }
  },
  created () {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    api.monitoringProgram(this.programId).then(program => {
      this.program = program
    })
  },
  methods: {
    deleteProgram() {
      api.deleteMonitoringProgram(this.programId).then(() => {
        this.$router.replace({ path: '/manage_programs' })
      }).catch(error => {
        console.log(error)
        alert('Delete failed.')
      })
    },
    handleSourceAction(action, source) {
      if(action === 'Remove') {
        this.sourceToRemove = source
      }
    },
    removeSource() {
      api.removeSourceFromMonitoringProgram(this.programId, this.sourceToRemove.id).then(() => {
        this.sourceToRemove = null
        this.$refs.sourceList.refresh()
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

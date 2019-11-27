<template>
  <div>
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load processing notes.
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <note-row inline-template v-for="note in notes"
        v-bind:key="note.id"
        v-bind:note="note"
        @deleted="refreshNotes">
        <div class="columns">
          <div class="column">
            <div class="spinner" v-if="state == 'updating' || state == 'deleting'">
              One moment…
            </div>
            <div class="card" v-if="state == 'init'">
              <header class="card-header">
                <p class="card-header-title">{{note.first_name}} {{note.last_name}}
                  <span style="font-weight: normal;">&nbsp;– {{formatDateTime(note.time_created)}}</span>
                </p>
                <div class="card-header-icon" v-if="note.editable">
                  <span class="icon link" aria-label="edit" @click="editNote">
                    <i class="fas fa-edit" aria-hidden="true"></i>
                  </span>
                  <span class="icon" aria-label="delete" @click="deleteNote">
                    <i class="fas fa-trash" aria-hidden="true"></i>
                  </span>
                </div>
              </header>
              <div class="card-content">
                <p style="white-space: pre;">{{note.notes}}</p>
              </div>
            </div>

            <fieldset :disabled="state == 'updating'" v-if="state == 'editing' || state == 'updating'">
              <div class="field">
                <div class="control">
                  <textarea class="textarea hasContent" v-model="newNotes" ref="notesField"></textarea>
                </div>
              </div>
              <button class="button is-primary" @click="updateNote">Update</button>
              <button class="button" @click="cancelEditNote">Cancel</button>
            </fieldset>
          </div>
        </div>
      </note-row>
      <p v-if="notes.length === 0" class="content">
        There are have been no notes recorded for this data source.
      </p>
      <div class="field">
        <div class="control">
          <textarea
            class="textarea"
            placeholder="Add notes about how this data was processed before uploading to the TSX web interface."
            rows="2"
            v-model="newNotes"
            v-bind:class="{ hasContent: newNotes.trim().length > 0 }"
            @focus="notesFocused = true"
            @blur="notesFocused = false">
          </textarea>
        </div>
      </div>
      <button class="button is-primary" v-if="showSubmit" :disabled="!enableSubmit" @click="submitNotes">Submit</button>

    </div>
  </div>
</template>

<script>
import * as api from '@/api'
import Vue from 'vue'

const Note = {
  data() {
    return {
      state: 'init',
      newText: ''
    }
  },
  computed: {
    isEditing: function() { return this.state === 'editing' }
  },
  created() {
  },
  methods: {
    editNote() {
      this.newNotes = this.note.notes
      this.state = 'editing'
      Vue.nextTick(() => {
        console.log(this.$refs.notesField[0])
        this.$refs.notesField[0].focus()
      })
    },
    cancelEditNote() {
      this.state = 'init'
    },
    deleteNote() {
      this.state = 'deleting'
      api.deleteDataSourceNote(this.note.id).then(() => {
        this.$emit('deleted')
      }).catch(error => {
        console.log(error)
        this.state = 'init'
        this.error = 'Delete failed'
      })
    },
    updateNote() {
      this.state = 'updating'
      api.updateDataSourceNote(this.note.id, this.newNotes).then(() => {
        this.note.notes = this.newNotes
        this.state = 'init'
      }).catch(error => {
        console.log(error)
        this.state = 'init'
        this.error = 'Updating notes failed'
      })
    },
    formatDateTime(str) {
      return new Date(Date.parse(str)).toLocaleString()
    }
  },
  props: {
    note: Object
  }
}

export default {
  name: 'ProcessingNotes',
  components: {
    'note-row': Note
  },
  data () {
    return {
      notes: [],
      newNotes: '',
      status: 'loading',
      submitStatus: 'init',
      notesFocused: false
    }
  },
  computed: {
    showSubmit: function() {
      return this.enableSubmit || this.notesFocused
    },
    enableSubmit: function() {
      return this.newNotes.trim().length > 0
    }
  },
  created() {
    this.refreshNotes()
  },
  methods: {
    refreshNotes() {
      this.status = 'loading'
      api.dataSourceNotes(this.sourceId).then((notes) => {
        this.notes = notes
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    submitNotes() {
      this.submitStatus = 'submitting'
      api.createDataSourceNotes(this.sourceId, this.newNotes).then(() => {
        this.newNotes = ''
        this.refreshNotes()
        this.submitStatus = 'init'
      }).catch((error) => {
        console.log(error)
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
textarea:focus, textarea.hasContent {
  min-height: 8em;
}
</style>

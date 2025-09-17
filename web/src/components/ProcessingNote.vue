<template>
  <div class="columns">
    <div class="column">
      <div
        v-if="state == 'updating' || state == 'deleting'"
        class="spinner"
      >
        One moment…
      </div>
      <div
        v-if="state == 'init'"
        class="card"
      >
        <header class="card-header">
          <p class="card-header-title">
            {{ note.first_name }} {{ note.last_name }}
            <span style="font-weight: normal; margin-left: 1em;">{{ formatDateTime(note.time_created) }}</span>
          </p>
          <div
            v-if="note.editable"
            class="card-header-icon"
          >
            <span
              class="icon link"
              aria-label="edit"
              @click="editNote"
            >
              <i
                class="fas fa-edit"
                aria-hidden="true"
              />
            </span>
            <span
              class="icon"
              aria-label="delete"
              @click="deleteNote"
            >
              <i
                class="fas fa-trash"
                aria-hidden="true"
              />
            </span>
          </div>
        </header>
        <div class="card-content">
          <p style="white-space: pre-wrap;">
            {{ note.notes }}
          </p>
        </div>
      </div>

      <fieldset
        v-if="state == 'editing' || state == 'updating'"
        :disabled="state == 'updating'"
      >
        <div class="field">
          <div class="control">
            <textarea
              ref="notesField"
              v-model="newNotes"
              class="textarea hasContent"
            />
          </div>
        </div>
        <div class="buttons">
          <button
            class="button is-primary"
            @click="updateNote"
          >
            Update
          </button>
          <button
            class="button"
            @click="cancelEditNote"
          >
            Cancel
          </button>
        </div>
      </fieldset>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { nextTick } from 'vue'

export default {
  props: {
    note: {
      type: Object,
      required: true
    }
  },
  emits: [ "deleted", "updated" ],
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
      nextTick(() => {
        this.$refs.notesField.focus()
      })
    },
    cancelEditNote() {
      this.state = 'init'
    },
    deleteNote() {
      this.state = 'deleting'
      api.deleteDataSourceNote(this.note.source_id, this.note.id).then(() => {
        this.$emit('deleted')
      }).catch(error => {
        console.log(error)
        this.state = 'init'
        this.error = 'Delete failed'
      })
    },
    updateNote() {
      this.state = 'updating'
      api.updateDataSourceNote(this.note.source_id, this.note.id, this.newNotes).then(() => {
        this.$emit('updated')
        this.state = 'init'
      }).catch(error => {
        console.log(error)
        this.state = 'init'
        this.error = 'Updating notes failed'
      })
    },
    formatDateTime(str) {
      let date = new Date(Date.parse(str))
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
    }
  }
}
</script>
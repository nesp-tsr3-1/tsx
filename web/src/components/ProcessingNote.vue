<template>
  <div class="columns">
    <div class="column">
      <div class="spinner" v-if="state == 'updating' || state == 'deleting'">
        One moment…
      </div>
      <div class="card" v-if="state == 'init'">
        <header class="card-header">
          <p class="card-header-title">{{note.first_name}} {{note.last_name}}
            <span style="font-weight: normal; margin-left: 1em;">{{formatDateTime(note.time_created)}}</span>
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
          <p style="white-space: pre-wrap;">{{note.notes}}</p>
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
</template>

<script>
export default {
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
        console.log(this.$refs.notesField[0])
        this.$refs.notesField[0].focus()
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
        this.note.notes = this.newNotes
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
  },
  props: {
    note: Object
  }
}
</script>
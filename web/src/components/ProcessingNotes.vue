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
      <note-row v-for="note in notes"
        v-bind:key="note.id"
        v-bind:note="note"
        @deleted="refreshNotes">
      </note-row>
      <p v-if="notes.length === 0" class="content">
        No notes have been recorded for this dataset.
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
import * as api from '../api.js'
import { nextTick } from 'vue'
import Note from './ProcessingNote.vue'

export default {
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
      api.createDataSourceNote(this.sourceId, this.newNotes).then(() => {
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

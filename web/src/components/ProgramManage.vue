<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Programs</h2>

          <div v-if="state === 'loading'">Loading...</div>

          <div v-if="state === 'error'">Something went wrong. Please try again later.</div>

          <div v-if="state === 'loaded'">
            <router-link to="/program/edit/new" tag="button" class="button is-primary">Create New Program</router-link>
            <hr>
            <program-list></program-list>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import ProgramList from './ProgramList.vue'

export default {
  name: 'ProgramManage',
  components: {
    'program-list': ProgramList
  },
  data () {
    return {
      state: 'loading'
    }
  },
  created () {
    this.state = 'loaded'
  },
  methods: {
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

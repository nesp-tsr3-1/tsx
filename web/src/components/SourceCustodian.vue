<template>
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
</template>

<script>
import * as api from '../api.js'

export default {
  data() {
    return {
      state: 'init'
    }
  },
  computed: {
    displayName() {
      let user = this.user
      if(user.first_name) {
        return user.first_name + ' ' + user.last_name
      } else {
        return ''
      }
    },
    isRegistered() {
      return this.user.first_name !== null
    }
  },
  created() {
  },
  methods: {
    deleteUser() {
      this.state = 'deleting'
      api.deleteDataSourceCustodian(this.sourceId, this.user.id).then(() => {
        this.$emit('deleted')
      }).catch(error => {
        console.log(error)
        this.state = 'init'
        this.error = 'Delete failed'
      })
    }
  },
  props: {
    user: Object,
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

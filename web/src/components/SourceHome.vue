<template>
  <div class="section">
    <div class="container source-home">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Datasets</h2>

          <div v-if="state === 'loading'">Loading...</div>

          <div v-if="state === 'error'">Something went wrong. Please try again later.</div>

          <div v-if="state === 'noAccess'" class="content">
            <p>Thank you for signing up for a TSX web account.</p>

            <p>Before you can upload data, a TSX administrator first needs to grant access to your account. Please contact tsx@uq.edu.au to request access or for further information.</p>
          </div>

          <div v-if="state === 'loaded'">
            <router-link to="/source/edit/new" tag="button" class="button is-primary">Create New Dataset</router-link>
            <hr>
            <source-list></source-list>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import * as api from '@/api'
import SourceList from '@/components/SourceList'

export default {
  name: 'SourceHome',
  components: {
    'source-list': SourceList
  },
  data () {
    return {
      currentUser: null,
      error: null
    }
  },
  created() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })

    api.currentUser().then(currentUser => {
      this.currentUser = currentUser
    }).catch(error => {
      this.error = error
    })
  },
  computed: {
    state() {
      if(this.error) {
        return 'error'
      } else if(this.currentUser === null) {
        return 'loading'
      } else if(this.currentUser.roles.some(x => x === 'Administrator' || x === 'Custodian')) {
        return 'loaded'
      } else {
        return 'noAccess'
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

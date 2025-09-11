<template>
  <div class="section">
    <div class="container source-home">
      <div class="columns">
        <div class="column">
          <user-nav />
          <h2 class="title">
            Datasets
          </h2>

          <div v-if="state === 'loading'">
            Loading...
          </div>

          <div v-if="state === 'error'">
            Something went wrong. Please try again later.
          </div>

          <div
            v-if="state === 'noAccess'"
            class="content"
          >
            <p>Thank you for signing up for a TSX web account.</p>

            <p>Before you can upload data, a TSX administrator first needs to grant access to your account. Please contact tsx@uq.edu.au to request access or for further information.</p>
          </div>

          <div v-if="state === 'loaded'">
            <router-link
              to="/datasets/edit/new"
              tag="button"
              class="button is-primary"
            >
              Create New Dataset
            </router-link>
            <hr>
            <source-list
              :show-agreement="showAgreement"
              @click-source="handleSourceClick"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import features from '../features.js'
import SourceList from './SourceList.vue'
import { handleLinkClick } from '../util.js'

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
  computed: {
    state() {
      if(this.error) {
        return 'error'
      } else if(this.currentUser === null) {
        return 'loading'
      } else if(this.currentUser.roles.some(x => x === 'Administrator' || x === 'Custodian' || x === 'Program manager')) {
        return 'loaded'
      } else {
        return 'noAccess'
      }
    },
    showAgreement() {
      return features.documents
    }
  },
  watch: {
    $route (to, from) {
      // This fixes a problem caused by KeepAlive when attempting to access the page and being redirected to login
      // This ensures that after logging in and returning to this page, we attempt to reload the current user
      if(to.name == 'SourceHome' && this.error) {
        this.reload()
      }
    }
  },
  created() {
    this.reload()
  },
  methods: {
    handleSourceClick(source, evt) {
      let url = "/datasets/" + source.id
      handleLinkClick(evt, url, this.$router)
    },
    reload() {
      this.error = false

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
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

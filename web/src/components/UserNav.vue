<template>
  <nav class="navbar" v-if="user">
    <div class="navbar-brand">
      <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="userNav" @click="toggleBurger" :class="{ 'is-active': burgerActive }">
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
    </div>
    <div id="userNav" class="navbar-menu" :class="{ 'is-active': burgerActive }">
      <div class="navbar-start"></div>
      <div class="navbar-end">
        <router-link
          class="navbar-item"
          :to="{ name: 'SourceHome' }">Datasets</router-link>
        <router-link
          class="navbar-item"
          v-if="canManageUsers"
          :to="{ name: 'UserManage' }">Manage Users</router-link>
        <router-link
          class="navbar-item"
          v-if="isProgramManager"
          :to="{ name: 'DataSubsetDownloads' }">Downloads</router-link>
        <router-link
          class="navbar-item"
          :to="{ name: 'CustodianFeedbackHome' }">Feedback</router-link>
        <router-link
          v-if="features.documents"
          class="navbar-item"
          :to="{ name: 'DataAgreementHome' }">Documents</router-link>

        <div class="navbar-item has-dropdown is-hoverable">
          <a class="navbar-link is-arrowless">
            <div class="button is-dark is-rounded">
              <span class="icon">
                <i class="far fa-question-circle"></i>
              </span>
              <span>Help</span>
            </div>
          </a>

          <div class="navbar-dropdown">
            <div class="navbar-item" style="white-space: initial; width: 18em;">
              <p>
                You can access our training
                manual and step-by-step
                video guides on how to use
                the TSX data management
                interface on our
                <a href="https://tsx.org.au/tsx-resources" target="_blank">TSX Resources page.</a>
              </p>
            </div>
            <div class="navbar-item" style="white-space: initial; width: 18em;">
              <p>
                Can’t find what you’re
                looking for? You can
                contact the TSX team
                directly at
                <a href="mailto:tsx@tern.org.au">tsx@tern.org.au</a>
              </p>
            </div>
          </div>
        </div>

        <router-link
              class="navbar-item"
              :to="{ name: 'Logout' }">Logout</router-link>


        <span
          class="navbar-item"
          style="color: #888">{{user.first_name}} {{user.last_name}}</span>
      </div>
    </div>

  </nav>
</template>

<script>
import * as api from '../api.js'
import features from '../features.js'
import { globalEventBus } from '../eventBus.js'

export default {
  name: 'UserNav',
  data () {
    return {
      status: 'loading',
      user: null,
      burgerActive: false,
      features,
      loginListener: null
    }
  },
  computed: {
    canManageUsers: function() {
      return this.user && this.user.is_admin
    },
    isProgramManager: function() {
      return this.user && (this.user.is_admin || this.user.roles.indexOf("Program manager") != -1)
    },
    canManagePrograms: function() {
      return this.user && this.user.is_admin
    }
  },
  created () {
    this.loginListener = globalEventBus.addListener('login', () => this.refresh())
    this.refresh()
  },
  unmounted() {
    this.loginListener.remove()
  },
  methods: {
    toggleBurger() {
      this.burgerActive = !this.burgerActive
    },
    refresh() {
      api.currentUser().then((user) => {
        this.user = user
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .navbar-item {
    color: hsl(217, 71%, 53%);
  }

  .navbar-item p {
    color: #333;
  }

  .router-link-active {
    font-weight:  bold;
  }
</style>

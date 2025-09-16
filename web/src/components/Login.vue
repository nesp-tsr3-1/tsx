<template>
  <div class="section">
    <div class="container is-widescreen login">
      <div style="margin-bottom: 1em; text-align: center;">
        <p
          v-if="after_signup"
          style="font-weight: bold; margin-bottom: 1em;"
        >
          Your account has been created
        </p>
        <p>Please enter your email address and password</p>
      </div>
      <form @submit.prevent="login">
        <fieldset :disabled="submitting">
          <div class="field">
            <label class="has-text-dark">Email address</label>
            <input
              v-model="email"
              v-autofocus
              class="input"
              type="text"
              placeholder="user@example.com"
            >
            <p
              v-if="errors.email"
              class="help is-danger"
            >
              {{ errors.email }}
            </p>
          </div>
          <div class="field">
            <label class="has-text-dark">Password</label>
            <input
              v-model="password"
              class="input"
              type="password"
            >
            <p
              v-if="errors.password"
              class="help is-danger"
            >
              {{ errors.password }}
            </p>
          </div>
          <button
            class="button is-primary"
            style="width: 100%; margin: 0.5em 0;"
          >
            Log In
          </button>
        </fieldset>
        <p style="font-size: 80%; text-align: center;">
          <router-link :to="{ path: '/reset_password', query: { email: email } }">
            Forgot password?
          </router-link>
        </p>
      </form>

      <p style="text-align: center">
        <router-link
          v-if="!after_signup"
          to="/signup"
        >
          <button
            class="button"
            style="margin-top: 2em;"
          >
            Create an account
          </button>
        </router-link>
      </p>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { globalEventBus } from '../eventBus.js'

export default {
  name: 'Login',
  data () {
    return {
      submitting: false,
      email: '',
      password: '',
      errors: {}
    }
  },
  computed: {
    after_signup () {
      return this.$route.query.after_signup
    }
  },
  methods: {
    login: function() {
      this.submitting = true
      api.login(this.email, this.password).then(response => {
        api.refreshCurrentUser()
        globalEventBus.dispatchEvent('login', {})
        this.$router.replace(this.$route.query.after_login || '/source')
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
        }
      }).finally(() => {
        this.submitting = false
      })
    }
  }
}
</script>

<style scoped>
.login {
  width: 100%;
  max-width: 24em !important;
  margin: 2em auto;
}

.login form {
  padding: 2em;
  background: white;
  box-shadow: 1px 1px 4px rgba(0,0,0,0.3);
}

fieldset {
  border: none;
}

fieldset:disabled {
  opacity: 0.7;
}
</style>
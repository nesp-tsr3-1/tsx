<template>
  <div class="section">
    <div class="container is-widescreen sign-up">
      <h3 class="title is-4">
        New Account
      </h3>
      <form>
        <fieldset :disabled="submitting">
          <div class="field">
            <label>First name</label>
            <input
              v-model="first_name"
              class="input"
              type="text"
              name="first_name"
              autofocus
            >
            <p
              v-if="errors.first_name"
              class="help is-warning"
            >
              {{ errors.first_name }}
            </p>
          </div>
          <div class="field">
            <label>Last name</label>
            <input
              v-model="last_name"
              class="input"
              type="text"
              name="last_name"
            >
            <p
              v-if="errors.last_name"
              class="help is-warning"
            >
              {{ errors.last_name }}
            </p>
          </div>
          <div class="field">
            <label>Email address</label>
            <input
              v-model="email"
              class="input"
              type="text"
              name="email"
              placeholder="e.g. user@example.com"
            >
            <p
              v-if="errors.email"
              class="help is-warning"
            >
              {{ errors.email }}
            </p>
          </div>
          <div class="field">
            <label>Contact phone number (optional)</label>
            <input
              v-model="phone_number"
              class="input"
              type="text"
              name="phone_number"
              placeholder="e.g. (01) 2345 6789, 0412 345 678"
            >
            <p
              v-if="errors.phone_number"
              class="help is-warning"
            >
              {{ errors.phone_number }}
            </p>
          </div>
          <hr>
          <div class="field">
            <label>Password</label>
            <input
              v-model="password"
              class="input"
              type="password"
              name="password"
            >
            <p
              v-if="errors.password"
              class="help is-warning"
            >
              {{ errors.password }}
            </p>
          </div>
          <div class="field">
            <label>Confirm password</label>
            <input
              v-model="confirm_password"
              class="input"
              type="password"
              name="confirm_password"
              @keyup.enter="signUp"
            >
            <p
              v-if="errors.confirm_password"
              class="help is-warning"
            >
              {{ errors.confirm_password }}
            </p>
          </div>
          <button
            type="button"
            class="button is-primary"
            style="margin: 0.5em 0;"
            @click="signUp"
          >
            {{ buttonLabel }}
          </button>
        </fieldset>
      </form>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'SignUp',
  data () {
    return {
      submitting: false,
      errors: {},
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      password: '',
      confirm_password: ''
    }
  },
  computed: {
    buttonLabel: function() {
      return this.submitting ? 'Please wait…' : 'Create Account'
    }
  },
  methods: {
    signUp: function() {
      if(this.submitting) {
        return
      }

      if(this.password !== this.confirm_password) {
        this.errors = { confirm_password: 'Passwords do not match' }
        return
      }

      this.submitting = true
      api.createUser({
        first_name: this.first_name,
        last_name: this.last_name,
        email: this.email,
        phone_number: this.phone_number,
        password: this.password
      }).then(response => {
        // Navigate to login with message
        this.$router.push({ path: 'login', query: { after_signup: true } })
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
        } else {
          this.errors = { 'server_error': true }
        }
      }).finally(() => {
        this.submitting = false
      })
    }
  }
}
</script>

<style scoped>
.sign-up {
  font-size: 100%;
  width: 100%;
  max-width: 40em;
  margin: 0 auto;
}
fieldset {
  border: none;
}
fieldset:disabled {
  opacity: 0.7;
}
</style>
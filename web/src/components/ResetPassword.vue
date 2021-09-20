<template>
  <div class="section">
    <div class="container is-widescreen forgot-password">
      <div v-if="resetSucceeded">
        <div style="margin-bottom: 1em; text-align: center;">
          <p>Your password has been successfully reset.</p>
          <p><router-link to="/login">Click here to login.</router-link></p>
        </div>
      </div>

      <!-- Password reset form once we have a reset code -->
      <div v-else-if="code">
        <div style="margin-bottom: 1em; text-align: center;">
          <p>Please enter your new password.</p>
        </div>
        <form v-on:submit.prevent="resetPassword">
          <fieldset v-bind:disabled="submitting">
            <div class="field">
              <label class="has-text-dark">Password</label>
              <input class="input" type="password" name="password" v-model="password" v-autofocus>
              <p class="help is-danger" v-if="errors.password">{{ errors.password }}</p>
            </div>
            <div class="field">
              <label class="has-text-dark">Confirm password</label>
              <input class="input" type="password" name="confirm_password" v-model="confirm_password">
              <p class="help is-danger" v-if="errors.confirm_password">{{ errors.confirm_password }}</p>
            </div>
            <button class="button is-primary" style="width: 100%; margin: 0.5em 0;" v-bind:disabled="!passwordsMatch" v-on:click="resetPassword">Set Password</button>

            <p v-if="errors.invalid_code" style="color: red;">
              Invalid reset code (expired or already used).
              <router-link to="/reset_password">Request another password reset.</router-link>
            </p>
            <p v-if="errors.server_error" style="color: red;">
              Something went wrong. Please try again later.
            </p>
          </fieldset>
        </form>
      </div>

      <!-- Request password reset form -->
      <div v-else-if="!resetEmailSent">
        <div style="margin-bottom: 1em; text-align: center;">
          <p>Please enter your email address.</p>
        </div>
        <form v-on:submit.prevent="requestPasswordReset">
          <fieldset v-bind:disabled="submitting">
            <div class="field">
              <label class="has-text-dark">Email address</label>
              <input class="input" type="text" placeholder="user@example.com" v-model="email" v-autofocus>
              <p class="help is-danger" v-if="errors.email">{{ errors.email }}</p>
            </div>
            <button class="button is-primary" style="width: 100%; margin: 0.5em 0;" v-on:click="requestPasswordReset">Request Password Reset</button>

            <p v-if="errors.server_error" style="color: red;">
              Something went wrong. Please try again later.
            </p>
          </fieldset>
        </form>
      </div>
      <div v-else="resetEmailSent">
        <div style="margin-bottom: 1em; text-align: center;">
          <p>An email containing instructions to reset your password has been sent to {{email}}.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'ResetPassword',
  data () {
    return {
      submitting: false,
      resetSucceeded: false,
      email: this.$route.query.email,
      code: this.$route.query.code,
      resetEmailSent: false,
      password: '',
      confirm_password: '',
      errors: {}
    }
  },
  watch: {
    '$route': function(val) {
      this.code = val.query.code
      this.errors = {}
    }
  },
  computed: {
    passwordsMatch: function() {
      return this.password === this.confirm_password
    }
  },
  methods: {
    requestPasswordReset: function() {
      if(this.submitting) {
        return
      }

      this.submitting = true
      api.requestPasswordReset(this.email).then(response => {
        this.resetEmailSent = true
        // this.$router.replace(this.$route.query.after_login || '/')
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
        }
      }).finally(() => {
        this.submitting = false
      })
    },
    resetPassword: function() {
      if(this.submitting) {
        return
      }

      if(this.password !== this.confirm_password) {
        this.errors = { confirm_password: 'Password must match' }
        return
      }

      this.submitting = true
      api.resetPassword(this.code, this.password).then(response => {
        this.resetSucceeded = true
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

<style>
.forgot-password {
  width: 100%;
  max-width: 24em !important;
  margin: 2em auto;
}

.forgot-password form {
  padding: 2em;
  background: white;
  /*border: 1px solid #eee;*/
  box-shadow: 1px 1px 4px rgba(0,0,0,0.3);
}

fieldset {
  border: none;
}

fieldset:disabled {
  opacity: 0.7;
}
</style>
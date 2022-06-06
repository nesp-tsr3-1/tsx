<template>
  <div class="section">
    <div class="container" style="max-with: 960px;"><div class="columns"><div class="column is-8 is-offset-2">
      <user-nav></user-nav>
      <h3 class="title is-4">Manage Account</h3>
      <div class="notification" v-if="message">{{ message }}</div>
      <form>
        <fieldset v-bind:disabled="formDisabled">
          <div class="field">
            <label>First name</label>
            <input class="input" type="text" name="first_name" v-model="first_name" autofocus>
            <p class="help is-danger" v-if="errors.first_name">{{ errors.first_name }}</p>
          </div>
          <div class="field">
            <label>Last name</label>
            <input class="input" type="text" name="last_name" v-model="last_name">
            <p class="help is-danger" v-if="errors.last_name">{{ errors.last_name }}</p>
          </div>
          <div class="field">
            <label>Email address</label>
            <input class="input" type="text" name="email" placeholder="e.g. user@example.com" v-model="email">
            <p class="help is-danger" v-if="errors.email">{{ errors.email }}</p>
          </div>
          <div class="field">
            <label>Contact phone number (optional)</label>
            <input class="input" type="text" name="phone_number" placeholder="e.g. (01) 2345 6789, 0412 345 678" v-model="phone_number">
            <p class="help is-danger" v-if="errors.phone_number">{{ errors.phone_number }}</p>
          </div>
          <!-- <hr> -->
          <!-- <div class="field">
            <label>Password</label>
            <input class="input" type="password" name="password" v-model="password">
            <p class="help is-danger" v-if="errors.password">{{ errors.password }}</p>
          </div>
          <div class="field">
            <label>Confirm password</label>
            <input class="input" type="password" name="confirm_password" v-model="confirm_password" v-on:keyup.enter="signUp">
            <p class="help is-danger" v-if="errors.confirm_password">{{ errors.confirm_password }}</p>
          </div>-->
          <button type="button" class="button is-primary" v-on:click='submit' style="margin: 0.5em 0;">{{ buttonLabel }}</button>
        </fieldset>
      </form>
    </div></div></div>
  </div>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'UserEdit',
  data () {
    return {
      errors: {},
      message: '',
      userId: null,
      state: 'loading', // loading, idle, error, submitting, submit_error
      first_name: '',
      last_name: '',
      email: '',
      phone_number: ''
      // password: '',
      // confirm_password: ''
    }
  },
  computed: {
    buttonLabel: function() {
      return this.state == 'submitting' ? 'Please wait…' : 'Update Account Details'
    },
    formDisabled: function() {
      return this.state == 'submitting' || this.state == 'loading'
    }
  },
  created() {
    api.currentUser().then((user) => {
      this.userId = user.id

      this.first_name = user.first_name
      this.last_name = user.last_name
      this.email = user.email
      this.phone_number = user.phone_number
      this.state = 'idle'
    })
  },
  methods: {
    submit: function() {
      if(this.state == 'submitting') {
        return
      }

      if(this.password !== this.confirm_password) {
        this.errors = { confirm_password: 'Passwords do not match' }
        return
      }

      this.message = ''
      this.state = 'submitting'
      this.errors = {}
      api.updateUser(this.userId, {
        first_name: this.first_name,
        last_name: this.last_name,
        email: this.email,
        phone_number: this.phone_number
      }).then(response => {
        this.message = 'User updated successfully'
        this.state = 'idle'
        // Navigate to login with message
        // this.$router.push({ path: 'login', query: { after_signup: true } })
      }).catch(error => {
        if(error.xhr.status === 400) {
          this.errors = JSON.parse(error.xhr.response)
        } else {
          this.errors = { 'server_error': true }
          this.message = 'Something went wrong while updating the user'
        }
        this.state = 'submit_error'
      })
    }
  }
}
</script>

<style>
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
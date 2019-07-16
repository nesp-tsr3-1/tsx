<template>
  <div class='login'>
    <div style="margin-bottom: 1em; text-align: center;">
      <p v-if="after_signup" style="font-weight: bold; margin-bottom: 1em;">Your account has been created</p>
      <p>Please enter your email address and password</p>
    </div>
    <form>
      <fieldset v-bind:disabled="submitting">
        <div class="field">
          <label class="has-text-dark">Email address</label>
          <input class="input" type="text" placeholder="user@example.com" v-model="email" autofocus></input>
          <p class="help is-danger" v-if="errors.email">{{ errors.email }}</p>
        </div>
        <div class="field">
          <label class="has-text-dark">Password</label>
          <input class="input" type="password" v-model="password"></input>
          <p class="help is-danger" v-if="errors.password">{{ errors.password }}</p>
        </div>
        <button class="button is-primary" style="width: 100%; margin: 0.5em 0;" v-on:click="login">Log In</button>
      </fieldset>
      <p style="font-size: 80%; text-align: center;"><a href="#">Forgot password?</a></p>
    </form>

    <p style="text-align: center">
      <router-link to="/signup" tag="button" class="button" style="margin-top: 2em;" v-if="!after_signup">Create an account</router-link>
      <!-- <button class="button" style="margin-top: 2em;">Create an account</button> -->
    </p>
  </div>
</template>

<script>
import * as api from '@/api'
// import * as util from '@/util'

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
        this.$router.replace(this.$route.query.after_login || '/')
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

<style>
/*label {
  display: block;
}
input {
  font-size: 100%;
  width: 100%;
  border: 1px solid #eee;
  padding: 0.5em;
}*/
/*.login input.input::placeholder {
  color: #888 !important;
}*/
.login {
  width: 100%;
  max-width: 24em;
  margin: 2em auto;
}

.login form {
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
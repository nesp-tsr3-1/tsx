<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Users</h2>
          <input class="input column is-6" type="text" placeholder="Search name or email" style="margin-bottom: 1em;" v-model="searchText">
          <table class="table" style="width: 100%">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              <user-row inline-template v-for="user in users" v-bind:key="user.id" v-bind:user="user">
                <tr>
                  <td>{{user.first_name}} {{user.last_name}}</td>
                  <td>{{user.email}}</td>
                  <td>
                    <fieldset v-bind:disabled="isLoading">
                      <div class="select" v-bind:class="{ 'is-loading': isLoading }">
                        <select v-model="clientRole">
                          <option>Administrator</option>
                          <option>Custodian</option>
                        </select>
                      </div>
                      <p v-if="isError" class="help is-danger">Failed to update role</p>
                    </fieldset>
                  </td>
                </tr>
              </user-row>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '@/api'

function debounce(fn, delay) {
  var timerId
  return function() {
    clearTimeout(timerId)
    var args = arguments
    var self = this
    timerId = setTimeout(function() {
      fn.apply(self, args)
    }, delay)
  }
}

function normalizedTerms() {
  return Array.from(arguments).flatMap(str => str.toLowerCase().replace(/[^a-z]/g, '').split(/ +/))
}

const UserRow = {
  data () {
    var currentRole = this.user.is_admin ? 'Administrator' : 'Custodian'
    return {
      clientRole: currentRole,
      serverRole: currentRole,
      state: 'init'
    }
  },
  computed: {
    isError: function() {
      return this.state === 'error'
    },
    isLoading: function() {
      return this.state === 'loading'
    }
  },
  watch: {
    clientRole(role) {
      if(this.state !== 'loading' && this.clientRole !== this.serverRole) {
        this.state = 'loading'

        api.currentUser().then((me) => {
          let proceed = true
          if(me.id === this.user.id && this.serverRole === 'Administrator' && this.clientRole !== 'Administrator') {
            proceed = confirm('You are about to remove Administrator privileges for yourself. Are you sure you wish to continue?')
          }

          if(proceed) {
            return api.updateUserRole(this.user.id, this.clientRole).then(() => {
              this.serverRole = this.clientRole
              this.state = 'init'
            })
          } else {
            this.clientRole = this.serverRole
            this.state = 'init'
          }
        }).catch((error) => {
          console.log(error)
          this.clientRole = this.serverRole // Revert UI
          this.state = 'error'
        })
      }
    }
  },
  props: {
    user: Object
  }
}

export default {
  name: 'UserManage',
  components: {
    'user-row': UserRow
  },
  data () {
    return {
      status: 'loading',
      allUsers: [],
      searchText: '',
      debouncedSearchText: ''
    }
  },
  computed: {
    users: function() {
      if(this.debouncedSearchText.trim().length === 0) {
        return this.allUsers
      }

      var searchTerms = normalizedTerms(this.debouncedSearchText)
      return this.allUsers.filter(function(user) {
        var userTerms = normalizedTerms(user.first_name, user.last_name, user.email)
        return userTerms.some(userTerm => searchTerms.some(searchTerm => userTerm.includes(searchTerm)))
      })
    }
  },
  watch: {
    searchText: debounce(function(searchText) {
      this.debouncedSearchText = searchText
    }, 500)
  },
  created () {
    api.users().then((users) => {
      users.forEach((user) => {
        user.serverRole = user.is_admin ? 'Administrator' : 'Custodian'
        user.clientRole = user.serverRole
      })
      this.allUsers = users
      this.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
    updateUserRole: function(user, role) {

    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

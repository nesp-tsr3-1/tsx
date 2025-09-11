<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav />
          <h2 class="title">
            Users
          </h2>
          <input
            v-model="searchText"
            class="input column is-6"
            type="text"
            placeholder="Search name or email"
            style="margin-bottom: 1em;"
          >
          <table
            class="table"
            style="width: 100%"
          >
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              <user-row
                v-for="user in users"
                :key="user.id"
                :user="user"
                :monitoring-programs="monitoringPrograms"
              />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import UserRow from './UserRow.vue'

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
  return Array.from(arguments).flatMap(str => (str || '').toLowerCase().replace(/[^a-z]/g, '').split(/ +/))
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
      debouncedSearchText: '',
      monitoringPrograms: []
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
        user.serverRole = user.role
        user.clientRole = user.serverRole
      })
      this.allUsers = users
      this.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      this.status = 'error'
    })

    api.monitoringPrograms().then(x => this.monitoringPrograms = x)
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

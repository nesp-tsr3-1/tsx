<template>
  <ul class='user-nav' v-if="user">
    <li><router-link :to="{ name: 'SourceHome' }">Datasets</router-link></li>
    <li v-if="canManageUsers"><router-link :to="{ name: 'UserManage' }">Manage Users</router-link></li>
    <li v-if="isProgramManager"><router-link :to="{ name: 'DataSubsetDownloads' }">Downloads</router-link></li>
    <li><router-link :to="{ name: 'Logout' }">Logout</router-link></li>
    <li style="color: #888">{{user.first_name}} {{user.last_name}}</li>
  </ul>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'UserNav',
  data () {
    return {
      status: 'loading',
      user: null
    }
  },
  computed: {
    canManageUsers: function() {
      return this.user && this.user.is_admin
    },
    isProgramManager: function() {
      return this.user && (this.user.is_admin || this.user.roles.indexOf("Program Manager") != -1)
    }
  },
  created () {
    api.currentUser().then((user) => {
      this.user = user
      this.status = 'loaded'
    }).catch((error) => {
      console.log(error)
      this.status = 'error'
    })
  },
  methods: {
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  ul.user-nav {
    text-align: right;
    margin-bottom: 1em;
  }

  ul li {
    display: inline-block;
    margin-left: 1em;
  }

  .router-link-active {
    font-weight:  bold;
  }
</style>

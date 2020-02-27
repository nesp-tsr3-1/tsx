<template>
  <ul class='user-nav' v-if="user">
    <li style="font-weight: bold;">{{user.first_name}}</li>
    <li><router-link :to="{ name: 'SourceHome' }">Datasets</router-link></li>
    <li v-if="canManageUsers"><router-link :to="{ name: 'UserManage' }">Manage Users</router-link></li>
    <li><router-link :to="{ name: 'Logout' }">Logout</router-link></li>
  </ul>

</template>

<script>
import * as api from '@/api'

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
  }

  ul li {
    display: inline-block;
    margin-left: 1em;
  }
</style>

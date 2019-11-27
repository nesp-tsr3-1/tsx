<template>
  <div class="section">
    <div class="container source-home">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Datasets</h2>
          <router-link to="/source/edit/new" tag="button" class="button is-primary">Create New Dataset</router-link>
          <!-- <router-link to="/tsx" tag="button" class="button is-primary">TSX</router-link> -->
          <hr>
          <source-list></source-list>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import * as api from '@/api'
import SourceList from '@/components/SourceList'

export default {
  name: 'SourceHome',
  components: {
    'source-list': SourceList
  },
  data () {
    // var data = { imports: [] }

    // api.dataImports().then((imports) => { data.imports = imports })

    // return data
    return {}
  },
  created() {
    api.isLoggedIn().then(isLoggedIn => {
      if(!isLoggedIn) {
        this.$router.replace({ path: '/login', query: { after_login: this.$route.path } })
      }
    })
    // api.dataSources().then(dataSources => {
    //   console.log(dataSources)
    // })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

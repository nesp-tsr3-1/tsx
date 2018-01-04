<template>
  <div class="import-home">
    <h2 class="title">Plots</h2>
    <router-link to="/import/new" tag="button" class="button is-primary">Import surveys</router-link>
    <router-link to="/plot" tag="button" class="button is-primary">Plots</router-link>
    <router-link to="/lpi" tag="button" class="button is-primary">LPI</router-link>
    <hr>
    <h2 class="subtitle">Imports in progress</h2>
    <import-list></import-list>
    <h2 class="subtitle">Completed imports</h2>
    <import-list completed></import-list>
  </div>

</template>

<script>
// import * as api from '@/api'
import ImportList from '@/components/ImportList'

export default {
  name: 'ImportHome',
  components: {
    'import-list': ImportList
  },
  data () {
    // var data = { imports: [] }

    // api.dataImports().then((imports) => { data.imports = imports })

    // return data
    return {}
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>

<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-offset-2 is-8">

          <h3 class="title is-4">Local Settings</h3>
          <p class="content">These settings apply to your current browser only</p>
          <form>
            <fieldset>
              <div class="field">
                <label><input disabled class="checkbox" type="checkbox" v-model="features.documents"> Enable documents functionality</label>
              </div>
            </fieldset>
          </form>

          <hr>
          <p class="content">
            <router-link to="/datasets">Home</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import features from '../features.js'

export default {
  name: 'LocalSettings',
  data () {
    return {
        features
    }
  },
  computed: {
  },
  methods: {
  }
}
</script>

<style scoped>

</style>

<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-offset-2 is-8">
          <h3 class="title is-4">
            Page Not Found
          </h3>

          <p class="content">
            <router-link :to="{ name: 'SourceHome' }">
              Home
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

export default {
  name: 'NotFound',
  data() {
    return {
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

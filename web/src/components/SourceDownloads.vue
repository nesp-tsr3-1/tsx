<template>
  <CommonDownloads
    :source-id="sourceId"
    :enable-state-filter="false"
    :enable-program-filter="false"
    :enable-management-filter="true">
    <template #criteria-title>
      <h3 class="title is-6">Filtering criteria for downloads and trends</h3>
    </template>
  </CommonDownloads>
</template>

<script>
import CommonDownloads from './CommonDownloads.vue'

export default {
  name: 'SourceDownloads',
  components: {
    CommonDownloads
  },
  props: {
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

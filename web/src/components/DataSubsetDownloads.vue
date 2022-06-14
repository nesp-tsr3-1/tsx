<template>
  <div class="section">
    <div class="container">
      <div class="columns">
        <div class="column is-8 is-offset-2">
          <user-nav></user-nav>
          <h2 class="title">Data Subset Download</h2>
          <CommonDownloads
            :enable-program-filter="true"
            :enable-state-filter="true"
            :enable-management-filter="true">
            <template #criteria-title>
              <h3 class="title is-5">1. Subset Criteria</h3>
              <p class="block">Data that meets <em>all</em> of the criteria selected below will be included in the subset download.</p>
            </template>
            <template #downloads-title>
              <h3 class="title is-5">2. Download Data Subset</h3>
            </template>
          </CommonDownloads>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonDownloads from './CommonDownloads.vue'

export default {
  name: 'DataSubsetDownloads',
  components: {
    CommonDownloads
  }
}
</script>

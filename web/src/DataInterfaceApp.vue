<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <KeepAlive include="SourceHome,CustodianFeedbackHome">
        <component :is="Component" />
      </KeepAlive>
    </router-view>
  </div>
</template>

<script>

import "tippy.js/dist/tippy.css"

export default {
  name: 'App'
}
</script>

<style lang="scss">
@import './style.scss'
</style>

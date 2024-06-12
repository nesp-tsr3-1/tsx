<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <KeepAlive include="SourceHome">
        <component :is="Component" />
      </KeepAlive>
    </router-view>
  </div>
</template>

<script>

import "tippy.js/dist/tippy.css"

export default {
  name: 'app'
}
</script>

<style lang="scss">
@import './style.scss'
</style>

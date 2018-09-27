<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'app'
}
</script>

<style lang="scss">

@import '~bulma/sass/utilities/initial-variables.sass';

// Colours from style guide:
$tsr-green: #387469;
$tsr-A: #7c5e77;
$tsr-B: #415866;
$tsr-C: #9e4c6e;
$tsr-D: #6899ae;
$tsr-E: #b45a65;
$tsr-F: #93b479;
$tsr-G: #636968;

$primary: $tsr-E;
$text: #fff;
$text-strong: #fff;
$label-color: #fff;
$background: $tsr-green;

body {
  background-color: $tsr-green;
}

.container {
  background-image: url('../static/images/bird-bg.png');
  background-repeat: no-repeat;
  background-position: top 1em left 2em;
  background-size: 150px;
}

$family-sans-serif: "Museo Sans", "Arial", BlinkMacSystemFont, -apple-system, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", "Helvetica", sans-serif;

$modal-background-background-color: rgba($black, 0.1);

@import "~bulma/bulma.sass";
@import '~bulma-tooltip';

.section {
  padding-top: 1em;
}

h1 {
  margin-top: 1em;
}

</style>

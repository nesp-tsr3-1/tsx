<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>

import "tippy.js/dist/tippy.css"

export default {
  name: 'app'
}
</script>

<style lang="scss">

@import '../node_modules/bulma/sass/utilities/initial-variables.sass';

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
$dark: $tsr-green;

// $text: #fff;
// $text-strong: #fff;
// $label-color: #fff;
// $background: $tsr-green;
// $body-background-color: $tsr-green;
// $table-background-color: $tsr-green;
// $table-color: #fff;
// $subtitle-color: #fff;
// $title-color: #fff;
// $table-striped-row-even-background-color: rgba(255,255,255,0.1) !default
// $table-striped-row-even-hover-background-color: rgba(255,255,255,0.2) !default
// $table-row-hover-background-color: rgba(255,255,255,0.2) !default


body {
  // background-color: $tsr-green;
}

// .bird-background {
//   background-image: url('../static/images/bird-bg.png');
//   background-repeat: no-repeat;
//   background-position: top 1em left 2em;
//   background-size: 150px;
// }

$family-sans-serif: "Museo Sans", "Arial", BlinkMacSystemFont, -apple-system, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", "Helvetica", sans-serif;

$input-disabled-background-color: white;

@import "../node_modules/bulma/bulma.sass";

input[disabled], select[disabled], textarea[disabled] {
  opacity: 0.7;
}

.section {
  padding-top: 1em;
}

h1 {
  margin-top: 1em;
}

.content h4 {
	font-weight: normal;
}

.is-dark {
	background-color: $tsr-green;
	color: white;
}

</style>

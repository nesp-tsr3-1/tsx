<template>
  <!-- <div class="field">
    <label class="label">{{field.label}}</label> -->
    <div class="buttons has-addons inline" style="flex-wrap: nowrap;">
      <button v-for="option in field.options"
        class="button is-small"
        :class="buttonClasses(option)"
        :disabled="option.disabled"
        @click="select(option)">{{option.label}}</button>
    </div>
  <!-- </div> -->
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'ButtonRadioField',
  data () {
    return {
    }
  },
  computed: {
    fieldValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('update:value', value)
      }
    }
  },
  created () {

  },
  methods: {
    select(option) {
      this.fieldValue = option.value
    },
    buttonClasses(option) {
      return {
        "is-selected": this.fieldValue == option.value,
      }
    }
  },
  props: {
    field: Object,
    value: null
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .label {
    color: #fff;
  }
  button:disabled {
    color: #555;
  }
  button.is-selected {
    background: #387469;
    color: white;
  }
</style>

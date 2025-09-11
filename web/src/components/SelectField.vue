<template>
  <div class="field">
    <label class="label">{{ field.label }}</label>
    <div class="select is-fullwidth">
      <select
        v-model="fieldValue"
        :disabled="field.disabled"
      >
        <option
          v-for="option in field.options"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'

export default {
  name: 'SelectField',
  props: {
    field: Object,
    value: null
  },
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
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .label {
    color: #fff;
  }
</style>

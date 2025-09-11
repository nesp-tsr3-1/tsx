<template>
  <div class="field">
    <label class="label">{{ field.label }}</label>
    <div v-for="option in field.options">
      <label>
        <input
          v-model="fieldValue"
          type="radio"
          :name="field.name"
          :value="option.value"
          :disabled="option.disabled"
        > {{ option.label }}
        <tippy
          v-if="option.help"
          class="info-icon icon"
          arrow
          interactive
          placement="right"
        >
          <template #default><i class="far fa-question-circle" /></template>
          <template #content>
            <div
              class="popup-content"
              v-html="option.help"
            />
          </template>
        </tippy>
      </label>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { Tippy } from 'vue-tippy'

export default {
  name: 'RadioField',
  components: {
    Tippy
  },
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
        console.log(value)
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

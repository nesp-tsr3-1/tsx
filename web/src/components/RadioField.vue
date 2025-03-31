<template>
  <div class="field">
    <label class="label">{{field.label}}</label>
    <div v-for="option in field.options">
      <label>
        <input type="radio" :name="field.name" :value="option.value" :disabled="option.disabled" v-model="fieldValue"> {{option.label}}
          <tippy class="info-icon icon" arrow interactive placement="right" v-if="option.help">
            <template #default><i class="far fa-question-circle"></i></template>
            <template #content>
              <div class="popup-content" v-html="option.help">
              </div>
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
</style>

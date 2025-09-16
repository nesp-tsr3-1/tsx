<template>
  <!-- TODO: merge this with SelectField -->
  <div
    class="field"
    style="color: #333"
  >
    <label class="label">{{ field.label }}</label>
    <div
      ref="field"
      class="is-fullwidth"
    >
      <Multiselect
        v-model="fieldValue"
        v-tippy="tooltip"
        :options="options"
        :searchable="true"
        placeholder="Select…"
        label="label"
        value-prop="value"
      />
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import Multiselect from '@vueform/multiselect'
import { directive } from 'vue-tippy'
import { useTippy } from 'vue-tippy'

export default {
  name: 'SelectField',
  components: {
    Multiselect
  },
  directives: {
    tippy: directive
  },
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: null,
      default: undefined
    }
  },
  emits: ["update:value"],
  data () {
    return {}
  },
  computed: {
    fieldValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('update:value', value)
      }
    },
    options() {
      return this.field.options.filter(option => option.value !== null && option.value !== undefined)
    },
    tooltip() {
      if(this.fieldValue == null) {
        return {
          content: 'Select a species',
          arrow: true,
          theme: 'yellow',
          placement: 'auto',
          trigger: 'manual',
          showOnCreate: true
        }
      } else {
        return undefined;
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
<style src="@vueform/multiselect/themes/default.css"></style>
<style>
  .tippy-box[data-theme~='yellow'] {
    background-color: gold;
    color: black;
    padding: 0.5em;
  }

  .tippy-box[data-theme~='yellow'][data-placement^='top'] > .tippy-arrow::before {
    border-top-color: gold;
  }
  .tippy-box[data-theme~='yellow'][data-placement^='bottom']
    > .tippy-arrow::before {
    border-bottom-color: gold;
  }
  .tippy-box[data-theme~='yellow'][data-placement^='left']
    > .tippy-arrow::before {
    border-left-color: gold;
  }
  .tippy-box[data-theme~='yellow'][data-placement^='right']
    > .tippy-arrow::before {
    border-right-color: gold;
  }

</style>
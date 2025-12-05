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
          :key="option.value"
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
export default {
  name: 'SelectField',
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
  emits: ['update:value'],
  data() {
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
  created() {

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

<template>
  <div :class="classes">
    <SelectField v-if="fieldType == 'select'" :field="field" v-model:value='fieldValue'></SelectField>
    <RadioField v-else-if="fieldType == 'radio'" :field="field" v-model:value='fieldValue'></RadioField>
    <ButtonRadioField v-else-if="fieldType == 'button-radio'" :field="field" v-model:value='fieldValue'></ButtonRadioField>
    <div v-else>(Unknown field type)</div>
  </div>
</template>

<script>
import * as api from '../api.js'
import SelectField from "./SelectField.vue"
import RadioField from "./RadioField.vue"
import ButtonRadioField from "./ButtonRadioField.vue"

export default {
  name: 'Field',
  components: {
    SelectField,
    RadioField,
    ButtonRadioField
  },
  data () {
    return {

    }
  },
  computed: {
    fieldType() {
      return this.field && this.field.type
    },
    fieldComponent() {
      fieldType = this.field && this.field.type
      if(fieldType === "select") {
        return SelectField
      } else {
        return null
      }
    },
    classes() {
      return "field-named-" + this.field.name
    },
    fieldValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('update:value', value)
      }
    }
  },
  props: {
    field: Object,
    value: null
  },
  emits: ['update:value']
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

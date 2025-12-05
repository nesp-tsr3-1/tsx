<template>
  <div :class="classes">
    <SelectField
      v-if="fieldType == 'select'"
      v-model:value="fieldValue"
      :field="field"
    />
    <SearchableSelectField
      v-else-if="fieldType == 'searchable-select'"
      v-model:value="fieldValue"
      :field="field"
    />
    <RadioField
      v-else-if="fieldType == 'radio'"
      v-model:value="fieldValue"
      :field="field"
    />
    <ButtonRadioField
      v-else-if="fieldType == 'button-radio'"
      v-model:value="fieldValue"
      :field="field"
    />
    <div v-else>
      (Unknown field type)
    </div>
  </div>
</template>

<script>
import SelectField from './SelectField.vue'
import SearchableSelectField from './SearchableSelectField.vue'
import RadioField from './RadioField.vue'
import ButtonRadioField from './ButtonRadioField.vue'

export default {
  name: 'GenericField',
  components: {
    SelectField,
    RadioField,
    ButtonRadioField,
    SearchableSelectField
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
  emits: ['update:value'],
  data() {
    return {

    }
  },
  computed: {
    fieldType() {
      return this.field && this.field.type
    },
    fieldComponent() {
      let fieldType = this.field && this.field.type
      if(fieldType === 'select') {
        return SelectField
      } else {
        return null
      }
    },
    classes() {
      return 'field-named-' + this.field.name
    },
    fieldValue: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('update:value', value)
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

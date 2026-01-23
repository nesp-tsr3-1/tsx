<template>
  <div class="text-input">
    <input
      ref="textInput"
      v-model="value"
      class="input"
      :placeholder="placeholder"
      @keydown="handleKeydown"
    >
    <div class="suggestions">
      <div
        v-for="suggestion in suggestions"
        :key="suggestion"
        class="suggestion"
        onmousedown="event.preventDefault(); return false;"
        @click="value = suggestion + ': '"
      >
        {{ suggestion }}:
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AutocompleteInput',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    items: {
      type: Array,
      required: true
    },
    placeholder: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {}
  },
  computed: {
    value: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    },
    suggestions() {
      // return this.items
      let search = this.modelValue.trim().toLowerCase()

      return this.items
        .map((x) => {
          let index = x.toLowerCase().indexOf(search)
          if(index >= 0) {
            return {
              value: x,
              sortKey: (index > 0) + x.toLowerCase()
            }
          } else {
            return null
          }
        })
        .filter(x => x)
        .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
        .map(x => x.value)
    }
  },
  methods: {
    handleKeydown(event) {
      let suggestions = this.suggestions
      if((event.key == 'Enter' || event.key == 'Tab') && suggestions.length == 1) {
        this.value = suggestions[0] + ': '
        event.preventDefault()
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

  .text-input {
    position: relative;
  }

.suggestions {
  display: none;
  flex-direction: column;
  align-items: flex-start;
  position: absolute;
  top: calc(100%);
  left: 0;
  background: white;
  border-radius: 5px;
  width: 100%;
  padding: 8px;
  box-shadow: 0 0 4px 0 rgba(0,0,0,0.3);
  z-index: 10000;
}

.suggestion {
  margin: 4px;
  background: #eee;
  padding: 4px;
  border-radius: 5px;
  cursor: pointer;
}

.text-input:has(input:focus) .suggestions:has(.suggestion) {
  display: flex;
}

</style>

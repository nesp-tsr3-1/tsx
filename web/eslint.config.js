import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'
import stylistic from '@stylistic/eslint-plugin'
import js from '@eslint/js'

export default [
  // add more generic rulesets here, such as:
  js.configs.recommended,
  stylistic.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    rules: {
      // override/add rules settings here, such as:
      // 'vue/no-unused-vars': 'error'
      // '@stylistic/function-call-spacing': ["error", "never"],
      '@stylistic/space-before-function-paren': ['error', 'never'],
      '@stylistic/comma-dangle': ['error', 'never'],
      '@stylistic/keyword-spacing': ['error', {
        overrides: {
          if: { after: false },
          for: { after: false },
          while: { after: false }
        }
      }],
      '@stylistic/brace-style': ['error', '1tbs', { allowSingleLine: true }],
      'no-use-before-define': ['error', { functions: false }],
      'no-empty': ['off'],
      'no-unused-vars': ['error', { caughtErrors: 'none', args: 'none' }]
    },
    plugins: {
      '@stylistic': stylistic
    },
    languageOptions: {
      sourceType: 'module',
      globals: {
        ...globals.browser
      }
    }
  }
]

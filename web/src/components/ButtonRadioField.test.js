import { expect, test, describe } from 'vitest'
import { mount } from '@vue/test-utils'
import ButtonRadioField from './ButtonRadioField.vue'

describe('ButtonRadioField', () => {
  const yesNoOptions = [
    {
      value: 'yes',
      label: 'Yes'
    },
    {
      value: 'no',
      label: 'No'
    }
  ]

  test('renders', () => {
    const wrapper = mount(ButtonRadioField, {
      props: {
        field: {
          options: yesNoOptions
        }
      }
    })
    expect(wrapper.get('button[data-test=\'yes\']').text()).toContain('Yes')
    expect(wrapper.get('button[data-test=\'no\']').text()).toContain('No')
  })

  test('initial value', () => {
    const wrapper = mount(ButtonRadioField, {
      props: {
        field: {
          options: yesNoOptions
        },
        value: 'yes'
      }
    })
    expect(wrapper.get('button[data-test=\'yes\']').classes()).toContain('is-selected')
  })

  test('handles click', async() => {
    const wrapper = mount(ButtonRadioField, {
      props: {
        field: {
          options: yesNoOptions
        }
      }
    })

    await wrapper.get('button[data-test=\'yes\']').trigger('click')
    await wrapper.get('button[data-test=\'no\']').trigger('click')

    expect(wrapper.emitted('update:value')).toEqual([['yes'], ['no']])
  })

  test('handles value update', async() => {
    const wrapper = mount(ButtonRadioField, {
      props: {
        field: {
          options: yesNoOptions
        }
      }
    })

    await wrapper.setProps({ value: 'yes' })
    expect(wrapper.get('button[data-test=\'yes\']').classes()).toContain('is-selected')
    expect(wrapper.get('button[data-test=\'no\']').classes()).not.toContain('is-selected')

    await wrapper.setProps({ value: 'no' })
    expect(wrapper.get('button[data-test=\'yes\']').classes()).not.toContain('is-selected')
    expect(wrapper.get('button[data-test=\'no\']').classes()).toContain('is-selected')
  })
})

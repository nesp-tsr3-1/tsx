import { vi, expect, test, describe } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CommonDownloads from './CommonDownloads.vue'

vi.mock('../api.js', () => {
  const species = [{
    id: 1,
    scientific_name: 'Testus sp.',
    common_name: 'Test species'
  }]

  return {
    async dataSubsetSites(params) {
      return [{ id: 1, name: 'Test site' }]
    },
    async dataSubsetSpecies(params) {
      return species
    },
    async currentUser() {
      return {
        id: 1,
        is_admin: true
      }
    },
    async species() {
      return species
    },
    async dataSubsetStats(params) {
      return {
        min_year: 1950,
        max_year: 2020,
        sighting_count: 100,
        taxon_count: 20,
        time_series_count: 30,
        source_count: 4,
        excluded_time_series_count: 5,
        excluded_time_series_taxon_count: 6
      }
    },
    async monitoringPrograms() {
      return [{
        id: 1,
        description: 'Test program'
      }]
    },
    async programsManagedBy(userId) {
      return [{
        id: 1,
        description: 'Test program'
      }]
    }
  }
})

vi.mock('../plotTrend.js', () => ({
  plotTrend() {},
  generateTrendPlotData() {},
  trendDiagnosticsText() {
    return ''
  }
}))

describe('CommonDownloads', () => {
  test('renders', async() => {
    const wrapper = mount(CommonDownloads, {
      props: {
        enableProgramFilter: true
      }
    })

    await flushPromises()

    expect(wrapper.get('[data-test=program-filter]').text()).toContain('Test program')

    await wrapper.get('[data-test=species-filter] .multiselect-search').trigger('focus')
    expect(wrapper.get('[data-test=species-filter] .multiselect-options').text()).toContain('Test species')

    await wrapper.get('[data-test=site-filter] .multiselect-search').trigger('focus')
    expect(wrapper.get('[data-test=site-filter] .multiselect-options').text()).toContain('Test site')
  })
})

<template>
  <div>
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load data summary
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <div v-if="items.length == 0">
        <p class="content">No records have been imported for this dataset.</p>
      </div>
      <div v-for="taxon in items">
        <table class="table is-fullwidth">
          <caption>
            <em>{{taxon.scientific_name}}</em> <span v-if="taxon.common_name">({{taxon.common_name}})</span>
          </caption>
          <thead>
            <tr>
              <th>Site</th>
              <th>Monitoring method</th>
              <th>Period of monitoring (years)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in taxon.ts">
              <td>{{t.site_name}}</td>
              <td>{{t.search_type}}</td>
              <td>{{t.min_year}}–{{t.max_year}}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="expander" v-if="showExpand">
        <button class="button is-light is-small" @click="expand">Show {{hiddenRowCount}} more rows</button>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'

let rowLimit = 10

export default {
  components: {
  },
  data () {
    return {
      status: 'loading',
      fullItems: [],
      truncatedItems: [],
      fullRowCount: 0,
      showAllItems: false
    }
  },
  computed: {
    items() {
      return this.showAllItems ? this.fullItems : this.truncatedItems
    },
    hiddenRowCount() {
      return this.fullRowCount - rowLimit
    },
    showExpand() {
      return !this.showAllItems && this.fullRowCount > rowLimit
    }
  },
  created() {
    this.refreshData()
  },
  methods: {
    refreshData() {
      this.status = 'loading'
      api.dataSourceSiteSummary(this.sourceId).then((items) => {
        this.fullItems = items
        this.fullRowCount = items.reduce((x, v) => x + v.ts.length, 0)

        this.showAllItems = this.fullRowCount <= rowLimit

        let limitedItems = []
        let maxLen = rowLimit
        for(let item of items) {
          let newItem = { ...item, ts: item.ts.slice(0, maxLen) }
          maxLen -= newItem.ts.length
          limitedItems.push(newItem)
          if(maxLen == 0) {
            break
          }
        }

        this.truncatedItems = limitedItems

        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    expand() {
      this.showAllItems = true
    }
  },
  props: {
    sourceId: Number
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
table {
  table-layout: fixed;
}
caption {
  margin-top: 1em;
  text-align: left;
  padding: 0 0.75em;
}
.expander {
  text-align: center;
  border-top: solid 1px #ddd;
}
</style>

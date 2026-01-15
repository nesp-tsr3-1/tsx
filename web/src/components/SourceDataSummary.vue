<template>
  <div ref="container">
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
        <p class="content">
          No records have been imported for this dataset.
        </p>
      </div>
      <div
        v-for="taxon in items"
        :key="taxon.id"
      >
        <div :id="taxon.id" />
        <div class="table-header">
          <div class="table-header-title">
            <em>{{ taxon.scientific_name }}</em> <span v-if="taxon.common_name">({{ firstCommonName(taxon) }})</span>
          </div>
          <div style="flex-grow: 1" />
          <div><span class="tag is-medium">{{ sourceId }}_{{ taxon.taxon_id }}</span></div>
          <ul
            v-if="showNavigationButtons"
            class="table-header-links"
          >
            <li v-if="true">
              <a
                href="#summary_top"
                title="Top of dataset summary"
              >
                <span
                  class="icon"
                  aria-label="top"
                >
                  <i
                    class="fas fa-fast-backward"
                    aria-hidden="true"
                  />
                </span>
              </a>
            </li>
            <li v-else>
              <span
                class="icon"
                aria-label="top"
              >
                <i
                  class="fas fa-fast-backward"
                  aria-hidden="true"
                />
              </span>
            </li>

            <li v-if="taxon.prevId">
              <a
                :href="'#' + taxon.prevId"
                title="Previous taxon"
              >
                <span
                  class="icon"
                  aria-label="prev"
                >
                  <i
                    class="fas fa-step-backward"
                    aria-hidden="true"
                  />
                </span>
              </a>
            </li>
            <li v-else>
              <span
                class="icon"
                aria-label="top"
                title="Previous taxon"
              >
                <i
                  class="fas fa-step-backward"
                  aria-hidden="true"
                />
              </span>
            </li>

            <li v-if="taxon.nextId">
              <a :href="'#' + taxon.nextId">
                <span
                  class="icon"
                  aria-label="top"
                  title="Next taxon"
                >
                  <i
                    class="fas fa-step-forward"
                    aria-hidden="true"
                  />
                </span>
              </a>
            </li>
            <li v-else>
              <span
                class="icon"
                aria-label="top"
              >
                <i
                  class="fas fa-step-forward"
                  aria-hidden="true"
                />
              </span>
            </li>

            <li v-if="true">
              <a href="#summary_bottom">
                <span
                  class="icon"
                  aria-label="top"
                  title="Bottom of dataset summary"
                >
                  <i
                    class="fas fa-fast-forward"
                    aria-hidden="true"
                  />
                </span>
              </a>
            </li>
            <li v-else>
              <span
                class="icon"
                aria-label="top"
              >
                <i
                  class="fas fa-fast-forward"
                  aria-hidden="true"
                />
              </span>
            </li>
          </ul>
        </div>
        <table class="table is-fullwidth">
          <thead>
            <tr>
              <th>Site</th>
              <th>Monitoring method</th>
              <th>Period of monitoring (years)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="[index, t] in taxon.ts.entries()"
              :key="index"
            >
              <td>{{ t.site_name }}</td>
              <td>{{ t.search_type }}</td>
              <td>{{ t.min_year }}–{{ t.max_year }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        v-if="showNavigationButtons"
        id="summary_bottom"
      >
        <p><em>End of summary</em></p>
        <ul
          v-if="showNavigationButtons"
          class="table-header-links"
        >
          <li>
            <a
              href="#summary_top"
              title="Top of dataset summary"
            >
              <span
                class="icon"
                aria-label="top"
              >
                <i
                  class="fas fa-fast-backward"
                  aria-hidden="true"
                />
              </span>
            </a>
          </li>

          <li>
            <a
              :href="'#' + lastTaxonId"
              title="Previous taxon"
            >
              <span
                class="icon"
                aria-label="prev"
              >
                <i
                  class="fas fa-step-backward"
                  aria-hidden="true"
                />
              </span>
            </a>
          </li>

          <li>
            <span
              class="icon"
              aria-label="top"
            >
              <i
                class="fas fa-step-forward"
                aria-hidden="true"
              />
            </span>
          </li>

          <li>
            <span
              class="icon"
              aria-label="top"
            >
              <i
                class="fas fa-fast-forward"
                aria-hidden="true"
              />
            </span>
          </li>
        </ul>
      </div>
      <div
        v-if="showExpand"
        class="expander"
      >
        <button
          class="button is-light is-small"
          @click="expand"
        >
          Show {{ hiddenRowCount }} more rows
        </button>
      </div>
      <div
        v-if="showCollapse"
        class="expander"
      >
        <button
          class="button is-light is-small"
          @click="collapse"
        >
          Collapse summary
        </button>
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
  props: {
    sourceId: {
      type: Number,
      required: true
    }
  },
  data() {
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
      return !this.showAllItems && this.exceedsRowLimit
    },
    showCollapse() {
      return this.showAllItems && this.exceedsRowLimit
    },
    showNavigationButtons() {
      return this.showAllItems && this.exceedsRowLimit
    },
    exceedsRowLimit() {
      return this.fullRowCount > rowLimit
    },
    lastTaxonId() {
      return this.fullItems.at(-1)?.id
    }
  },
  created() {
    this.refresh()
  },
  methods: {
    refresh() {
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

        var prevItem = null
        for(let item of items) {
          item.id = 'summary_' + item.taxon_id
          item.prevId = prevItem?.id
          if(prevItem) {
            prevItem.nextId = item.id
          }
          prevItem = item
        }

        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    expand() {
      this.showAllItems = true
    },
    collapse() {
      this.showAllItems = false
      this.$refs.container.scrollIntoView(true)
    },
    firstCommonName(taxon) {
      return taxon.common_name.split(',')[0]
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
table {
  table-layout: fixed;
  overflow-wrap: break-word;
}
caption {
  margin-top: 1em;
  margin-bottom: 1em;
  text-align: left;
}
caption .notification {
  padding: 1em 0.75em;
  font-weight: bold;
}
.table-header {
  display: flex;
  gap: 0.5em;
  justify-content: space-between;
  align-items: center;
  padding: 1em 0.75em;
  margin-top: 1em;
  margin-bottom: 1em;
  position: sticky;
  top: 0;
  background: #eee;
}
.table-header-title {
  font-weight: bold;
}
ul.table-header-links {
  display: flex;
  gap: 0em;
  color: #aaa;
}
ul.table-header-links a {
  color: #333;
}

.expander {
  text-align: center;
  border-top: solid 1px #ddd;
}

#summary_bottom {
  display: flex;
  background: #eee;
  padding: 1em 0.75em;
  justify-content: space-between;
}
</style>

<template>
  <div ref="container">
    <div v-if="status == 'loading'">
      <p>
        Loading…
      </p>
    </div>
    <div v-if="status == 'error'">
      <p>
        Failed to load history
      </p>
    </div>
    <div v-if="status == 'loaded'">
      <div v-if="items.length == 0">
        <p class="content">
          No history for this dataset.
        </p>
      </div>
      <div
        v-for="item in items"
        :key="item.id"
      >
        <details>
          <summary class="block">
            <strong>{{ formatDateTime(item.time_recorded) }}</strong> <strong>{{ item.action_description }}</strong> by <strong>
              {{ item.user.first_name }}
              {{ item.user.last_name }}
            </strong>
          </summary>

          <div style="margin-bottom: 2em">
            <table
              v-if="item.action_name == 'CREATE_SOURCE'"
              class="table"
            >
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="field in item.data?.fields"
                  :key="field.name"
                >
                  <td><b>{{ field.label }}</b></td>
                  <td>{{ field.new_value ?? '(None)' }}</td>
                </tr>
              </tbody>
            </table>

            <div v-if="item.action_name == 'UPDATE_SOURCE'">
              <table
                v-if="item.has_changes"
                class="table"
              >
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>Old Value → New Value</th>
                  </tr>
                </thead>
                <tbody>
                  <template
                    v-for="field in item.data?.fields"
                    :key="field.name"
                  >
                    <tr v-if="field.old_value !== field.new_value">
                      <td><b>{{ field.label }}</b></td>
                      <td>{{ field.old_value ?? '(None)' }} → {{ field.new_value ?? '(None)' }}</td>
                    </tr>
                  </template>
                </tbody>
              </table>
              <p
                v-if="!item.has_changes"
                class="content"
              >
                No changes recorded.
              </p>
            </div>

            <table
              v-if="item.action_name == 'ADD_CUSTODIAN' || item.action_name == 'REMOVE_CUSTODIAN'"
              class="table"
            >
              <tbody>
                <tr v-if="item.data.custodian.first_name">
                  <th>First name</th>
                  <td>{{ item.data.custodian.first_name }}</td>
                </tr>
                <tr v-if="item.data.custodian.last_name">
                  <th>Last name</th>
                  <td>{{ item.data.custodian.last_name }}</td>
                </tr>
                <tr>
                  <th>Email address</th>
                  <td>{{ item.data.custodian.email }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script>
import * as api from '../api.js'
import { formatDateTime } from '../util.js'

function actionDescription(name) {
  switch (name) {
    case 'CREATE_SOURCE': return 'Dataset created'
    case 'UPDATE_SOURCE': return 'Dataset updated'
    case 'ADD_CUSTODIAN': return 'Custodian added'
    case 'REMOVE_CUSTODIAN': return 'Custodian removed'
    default: return name
  }
}

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
      items: []
    }
  },
  created() {
    this.refresh()
  },
  methods: {
    refresh() {
      this.status = 'loading'
      api.dataSourceHistory(this.sourceId).then((items) => {
        this.items = items.map(item => ({
          ...item,
          action_description: actionDescription(item.action_name),
          has_changes: item.data?.fields?.some(x => x.old_value !== x.new_value)
        }))
        this.status = 'loaded'
      }).catch((error) => {
        console.log(error)
        this.status = 'error'
      })
    },
    formatDateTime
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>

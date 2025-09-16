<template>
  <tr>
    <td>{{ user.first_name }} {{ user.last_name }}</td>
    <td>{{ user.email }}</td>
    <td>
      <fieldset :disabled="isLoading">
        <div
          class="select"
          :class="{ 'is-loading': isLoading }"
        >
          <select v-model="clientRole">
            <option>Administrator</option>
            <option>Program manager</option>
            <option>Custodian</option>
          </select>
        </div>
        <p
          v-if="isError"
          class="help is-danger"
        >
          Failed to update role
        </p>
        <div v-if="clientRole === 'Program manager'">
          <div
            v-for="program in clientPrograms"
            :key="program.id"
          >
            <label><input
              v-model="program.selected"
              type="checkbox"
            > {{ program.description }}</label>
          </div>
        </div>
      </fieldset>
    </td>
  </tr>
</template>

<script>

import * as api from '../api.js'

export default {
  name: 'UserRow',
  props: {
    user: {
      type: Object,
      required: true
    },
    monitoringPrograms: {
      type: Array,
      required: true
    }
  },
  data () {
    var currentRole = this.user.role
    return {
      clientRole: currentRole,
      serverRole: currentRole,
      state: 'init',
      clientPrograms: [],
      serverPrograms: []
    }
  },
  computed: {
    isError: function() {
      return this.state === 'error'
    },
    isLoading: function() {
      return this.state === 'loading'
    }
  },
  watch: {
    clientRole(role) {
      if(this.state !== 'loading' && this.clientRole !== this.serverRole) {
        this.state = 'loading'

        api.currentUser().then((me) => {
          let proceed = true
          if(me.id === this.user.id && this.serverRole === 'Administrator' && this.clientRole !== 'Administrator') {
            proceed = confirm('You are about to remove Administrator privileges for yourself. Are you sure you wish to continue?')
          }

          if(proceed) {
            return api.updateUserRole(this.user.id, this.clientRole).then(() => {
              this.serverRole = this.clientRole
              this.state = 'init'
              this.loadPrograms()
            })
          } else {
            this.clientRole = this.serverRole
            this.state = 'init'
          }
        }).catch((error) => {
          console.log(error)
          this.clientRole = this.serverRole // Revert UI
          this.state = 'error'
        })
      }
    },
    clientPrograms: {
    	handler(val) {
	    	function selectedProgramIds(ps) {
	    		return ps.filter(p => p.selected).map(p => p.id)
	    	}
	    	function copy(x) {
	    		return JSON.parse(JSON.stringify(x))
	    	}
	    	var clientIds = selectedProgramIds(this.clientPrograms)
	    	var serverIds = selectedProgramIds(this.serverPrograms)

	    	if(clientIds.join() != serverIds.join()) {
	    		api.updateProgramsManagedBy(this.user.id, clientIds).then(x => {
	    			this.serverPrograms = copy(this.clientPrograms)
	    		}).catch(x => {
	    			this.clientPrograms = copy(this.serverPrograms)
	    		})
	    	}
	    },
	    deep: true
	  }
  },
  created: function() {
  	this.loadPrograms()
  },
  methods: {
  	loadPrograms: function() {
  		if(this.clientRole == 'Program manager') {
  			api.programsManagedBy(this.user.id).then(x => {
  				this.serverPrograms = this.programModels(x)
  				this.clientPrograms = this.programModels(x)
  			})
  		} else {
  			this.serverPrograms = this.programModels([])
  			this.clientPrograms = this.programModels([])
  		}
  	},
  	programModels: function(selectedPrograms) {
			return this.monitoringPrograms.map(p => ({
				id: p.id,
				description: p.description,
				selected: selectedPrograms.filter(p2 => p.id === p2.id).length > 0
			}))
  	}
  }
}
</script>

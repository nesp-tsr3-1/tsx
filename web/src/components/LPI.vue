<template>
  <div class='plot content'>
    <h3 class='title'>LPI Plots</h3>
    <router-link to='/'>Back to imports</router-link>
    <hr>

    <table class='table is-fullwidth'>
      <thead>
        <tr>
          <th>Group</th>
          <th>Subgroup</th>
          <th>State</th>
          <th>StatusAuthority</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <basic-select :options='groupList' :selected-option='selectedGroup' @select='onGroupSelect'>
            </basic-select>
          </td>
          
          <td>
            <basic-select :options='subGroupList' :selected-option='selectedSubGroup' @select='onSubGroupSelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='stateList' :selected-option='selectedState' @select='onStateSelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='statusAuthorityList' :selected-option='selectedStateAuthority' @select='onStatusAuthoritySelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='statusList' :selected-option='selectedStatus' @select='onStatusSelect'>
            </basic-select>
          </td>


        </tr>
      </tbody>
    </table>

    <p>
      <button class='button is-primary' v-on:click='updatePlot' :disabled='loadingData'>Update</button>
    </p>
    <spinner size='large' message='Loading data....' v-show='loadingData'></spinner>
    <img v-bind:src="lpi1PlotUrl" class="my-lpi1-image" alt="No data"></img>
    <img v-bind:src="lpi2PlotUrl" class="my-lpi2-image" alt=""></img>
    <div></div>
    <img v-bind:src="infilePlitUrl" class="my-infile-image" alt=""></img>
    
  </div>
</template>
<script>
import * as api from '@/api'
import Spinner from 'vue-simple-spinner'
import { BasicSelect } from 'vue-search-select'
// import * as util from '@/util'
export default {
  name: 'LPI',
  components: {
    Spinner, BasicSelect
  },
  data () {
    var data = {
      baseLPIURL: 'https://nesp-dev1.coesra.org.au/lpi/',
      // group
      groupList: [],
      selectedGroup: {value: 'None', text: 'All'},
      // subgroup
      subGroupList: [],
      selectedSubGroup: {value: 'None', text: 'All'},
      // states
      stateList: [],
      selectedState: {value: 'None', text: 'All'},
      // status auth
      statusAuthorityList: [],
      selectedStateAuthority: {value: 'None', text: 'All'},
      // status
      statusList: [],
      selectedStatus: {value: 'None', text: 'All'},
      // is loading dataset
      loadingData: false,
      lpi1PlotUrl: 'https://nesp-dev1.coesra.org.au/lpi/all/Rplots0.png',
      lpi2PlotUrl: 'https://nesp-dev1.coesra.org.au/lpi/all/Rplots1.png',
      infilePlitUrl: 'https://nesp-dev1.coesra.org.au/lpi/all/nesp_infile_dtemp_array_plot.png'
    }
    // groups
    data.groupList.push({value: 'None', text: 'All'})
    data.groupList.push({value: 'Terrestrial', text: 'Terrestrial'})
    data.groupList.push({value: 'Wetland', text: 'Wetland'})
    data.groupList.push({value: 'Marine', text: 'Marine'})
    data.groupList.push({value: 'Shoreline (migratory)', text: 'Shoreline (migratory)'})
    data.groupList.push({value: 'Shoreline (resident)', text: 'Shoreline (resident)'})
    // subgroups
    data.subGroupList.push({value: 'None', text: 'All'})
    data.subGroupList.push({value: 'Tropicbirds Frigatebirds Gannets Boobies', text: 'Tropicbirds Frigatebirds Gannets Boobies'})
    data.subGroupList.push({value: 'Gulls Terns Noddies Skuas Jaegers', text: 'Gulls Terns Noddies Skuas Jaegers'})
    data.subGroupList.push({value: 'Rainforest', text: 'Rainforest'})
    data.subGroupList.push({value: 'Penguins', text: 'Penguins'})
    data.subGroupList.push({value: 'Tropical savanna woodland', text: 'Tropical savanna woodland'})
    data.subGroupList.push({value: 'Island endemic', text: 'Island endemic'})
    data.subGroupList.push({value: 'Petrels and Shearwaters', text: 'Petrels and Shearwaters'})
    data.subGroupList.push({value: 'Grassland', text: 'Grassland'})
    data.subGroupList.push({value: 'Albatrosses and Giant-Petrels', text: 'Albatrosses and Giant-Petrels'})
    data.subGroupList.push({value: 'Dry sclerophyll woodland/forest', text: 'Dry sclerophyll woodland/forest'})
    data.subGroupList.push({value: 'Arid Woodland/ shrubland', text: 'Arid Woodland/ shrubland'})
    data.subGroupList.push({value: 'Parrots, Lorikeets, Rosellas, Cockatoos, Corellas', text: 'Parrots, Lorikeets, Rosellas, Cockatoos, Corellas'})
    data.subGroupList.push({value: 'Heathland', text: 'Heathland'})
    data.subGroupList.push({value: 'Mallee woodland', text: 'Mallee woodland'})
    // states filter
    data.stateList.push({value: 'None', text: 'All'})
    data.stateList.push({value: 'Australian Capital Territory', text: 'Australian Capital Territory'})
    data.stateList.push({value: 'Commonwealth', text: 'Commonwealth'})
    data.stateList.push({value: 'Queensland', text: 'Queensland'})
    data.stateList.push({value: 'New South Wales', text: 'New South Wales'})
    data.stateList.push({value: 'Northern Territory', text: 'Northern Territory'})
    data.stateList.push({value: 'South Australia', text: 'South Australia'})
    data.stateList.push({value: 'Western Australia', text: 'Western Australia'})
    data.stateList.push({value: 'Tasmania', text: 'Tasmania'})
    data.stateList.push({value: 'Victoria', text: 'Victoria'})
    // status auth
    data.statusAuthorityList.push({value: 'None', text: 'All'})
    data.statusAuthorityList.push({value: 'EPBC', text: 'EPBC'})
    data.statusAuthorityList.push({value: 'IUCN', text: 'IUCN'})
    data.statusAuthorityList.push({value: 'BirdLifeAustralia', text: 'BifeLife Australia'})
    // status
    api.status().then((statusList) => {
      data.statusList = statusList.map(i => { return {value: i['description'], text: i['description']} })
      data.statusList.push({value: 'None', text: 'All'})
    })
    return data
  },
  methods: {
    updatePlot: function() {
      this.loadingData = true
      var filters = ''
      if(this.selectedGroup.value !== 'None') {
        filters = filters + 'group-' + encodeURI(this.selectedGroup.value + '_')
      }
      if(this.selectedSubGroup.value !== 'None') {
        filters = filters + 'subgroup-' + encodeURI(this.selectedSubGroup.value + '_')
      }
      if(this.selectedState.value !== 'None') {
        filters = filters + 'state-' + encodeURI(this.selectedState.value + '_')
      }
      if(this.selectedStateAuthority.value !== 'None') {
        filters = filters + 'statusauth-' + encodeURI(this.selectedStateAuthority.value + '_')
      }
      if(this.selectedStatus.value !== 'None') {
        filters = filters + 'status-' + encodeURI(this.selectedStatus.value + '_')
      }
      if (filters === '') {
        filters = 'all'
      }
      this.lpi1PlotUrl = this.baseLPIURL + filters + '/Rplots0.png'
      this.lpi2PlotUrl = this.baseLPIURL + filters + '/Rplots1.png'
      this.infilePlitUrl = this.baseLPIURL + filters + '/nesp_infile_dtemp_array_plot.png'
      console.log(this.lpi1PlotUrl)
      this.loadingData = false
    }, // end updatePlot function
    onGroupSelect: function(aGroup) {
      console.log('new group selected')
      this.selectedGroup = aGroup
      console.log(this.selectedGroup)
      if (this.selectedGroup.value === 'None') {
        this.selectedSubGroupDisabled = true
        this.selectedSubGroup = {value: 'None', text: 'All'}
      }
    }, // end onSourceSelect
    onSubGroupSelect: function(aSubGroup) {
      this.selectedSubGroup = aSubGroup
    }, // end onSourceSelect
    onStateSelect: function(aState) {
      this.selectedState = aState
    },
    onStatusAuthoritySelect: function(aStatusAuthority) {
      this.selectedStatusAuthority = aStatusAuthority
      if (this.selectedStatusAuthority.value === 'None') {
        this.selectedStatus = {value: 'None', text: 'All'}
        this.selectedStatusDisabled = true
        // this.selectedStatus.disable
      }
    }, // end onSourceSelect
    onStatusSelect: function(aStatus) {
      this.selectedStatus = aStatus
    }
  }
}
</script>

<style>
  .my-select {
    width: 240px;
  }
  .my-lpi1-image {
    width: 600px;
    height: 500px;
  }
  .my-lpi2-image {
    width: 700px;
    height: 500px;
  }
  .my-infile-image {
    width: 800px;
    height: 400px;
  }
</style>
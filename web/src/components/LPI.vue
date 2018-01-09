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
          <th>Reference Year</th>
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
            <basic-select :options='statusAuthorityList' :selected-option='selectedStatusAuthority' @select='onStatusAuthoritySelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='statusList' :selected-option='selectedStatus' @select='onStatusSelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='yearList' :selected-option='selectedYear' @select='onYearSelect'>
            </basic-select>
          </td>


        </tr>
      </tbody>
    </table>

    <p>
      <button class='button is-primary' v-on:click='updatePlot' :disabled='loadingData'>Update</button>
    </p>
    <spinner size='large' message='Loading data....' v-show='loadingData'></spinner>
    <canvas ref='lpiplot' class='big-plot'></canvas>
    <canvas ref='dotplot' class='big-plot'></canvas>
    <canvas ref='summaryplot'></canvas>
    <canvas ref='lambdaplot'></canvas>
  </div>
</template>
<script>
import * as api from '@/api'
import Chart from 'chart.js'
import Spinner from 'vue-simple-spinner'
import { BasicSelect } from 'vue-search-select'
// import * as util from '@/util'
// import _ from 'underscore'
export default {
  name: 'LPI',
  components: {
    Spinner, BasicSelect
  },
  data () {
    var data = {
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
      selectedStatusAuthority: {value: 'Max', text: 'Max'},
      // status
      statusList: [],
      selectedStatus: {value: 'None', text: 'All'},
      // year
      yearList: [],
      selectedYear: {value: '1970', text: '1970'},
      // is loading dataset
      // chart
      dotPlot: null,
      // chart data
      dotPlotDataSet: null,
      // lpi plot
      lpiPlot: null,
      lpiPlotDataSet: null,
      loadingData: false
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
    data.statusAuthorityList.push({value: 'Max', text: 'Max'})
    data.statusAuthorityList.push({value: 'EPBC', text: 'EPBC'})
    data.statusAuthorityList.push({value: 'IUCN', text: 'IUCN'})
    data.statusAuthorityList.push({value: 'BirdLifeAustralia', text: 'BifeLife Australia'})
    // year
    data.yearList.push({value: '1970', text: '1970'})
    data.yearList.push({value: '1980', text: '1980'})
    data.yearList.push({value: '1990', text: '1990'})
    data.yearList.push({value: '2000', text: '2000'})
    // status
    data.statusList.push({value: 'None', text: 'All'})
    data.statusList.push({value: 'Least Concern', text: 'Least Concern'})
    data.statusList.push({value: 'Near Threatened', text: 'Near Threatened'})
    data.statusList.push({value: 'Vulnerable', text: 'Vulnerable'})
    data.statusList.push({value: 'Endangered', text: 'Endangered'})
    data.statusList.push({value: 'Critically Endangered', text: 'Critically Endangered'})
    data.statusList.push({value: 'Critically Endangered (possibly extinct)', text: 'Critically Endangered (possibly extinct)'})
    data.statusList.push({value: 'Extinct', text: 'Extinct'})
    // return data
    return data
  },
  mounted: function() {
    var that = this
    // ---------- dot plot -------------
    this.dotPlotDataSet = {
      animation: {
        duration: 10000
      },
      datasets: [{
        label: 'count>0',
        backgroundColor: '#4dc9f6',
        borderColor: 'black',
        borderWidth: 1,
        data: [] },
      {
        label: 'count==0',
        backgroundColor: '#4dc906',
        borderColor: 'black',
        borderWidth: 1,
        data: [] }]
    }
    var ctx = this.$refs.dotplot.getContext('2d')
    this.dotPlot = new Chart(ctx, {
      type: 'bubble',
      data: that.dotPlotDataSet,
      // Configuration options go here
      options: {
        responsive: true,
        title: {
          display: true,
          text: 'Dot plots'
        },
        tooltips: {
          mode: 'point'
        }
      }
    })
    // --------- lpi plot ------------
    this.lpiPlotDataSet = {
      labels: [],
      datasets: [{
        label: 'LPI_final',
        borderColor: 'black',
        fill: false,
        data: [] },
      {
        label: 'CI_Low',
        borderColor: '#3e95cd',
        fill: 1,
        data: [] },
      {
        label: 'CI_High',
        borderColor: '#3e95cd',
        fill: 1,
        data: [] }]
    }
    var lpiPlotCtx = this.$refs.lpiplot.getContext('2d')
    this.lpiPlot = new Chart(lpiPlotCtx, {
      type: 'line',
      data: that.lpiPlotDataSet,
      // Configuration options go here
      options: {
        responsive: true,
        title: {
          display: true,
          text: 'LPI plot'
        }
      }
    })
  },
  methods: {
    updatePlot: function() {
      this.loadingData = true
      var filtersStr = ''
      var filterParams = {}
      if(this.selectedGroup.value !== 'None') {
        filtersStr = filtersStr + 'group-' + this.selectedGroup.value + '_'
        filterParams['group'] = this.selectedGroup.value
      }
      if(this.selectedSubGroup.value !== 'None') {
        filtersStr = filtersStr + 'subgroup-' + this.selectedSubGroup.value + '_'
        filterParams['subgroup'] = this.selectedSubGroup.value
      }
      if(this.selectedState.value !== 'None') {
        filtersStr = filtersStr + 'state-' + this.selectedState.value + '_'
        filterParams['state'] = this.selectedState.value
      }
      if(this.selectedStatusAuthority.value !== 'None') {
        filtersStr = filtersStr + 'statusauth-' + this.selectedStatusAuthority.value + '_'
        filterParams['statusauth'] = this.selectedStatusAuthority.value
      }
      if(this.selectedStatus.value !== 'None') {
        filtersStr = filtersStr + 'status-' + this.selectedStatus.value
        filterParams['status'] = this.selectedStatus.value
      }
      filterParams['format'] = 'dotplot'
      console.log(filtersStr)
      console.log(filterParams)
      var that = this
      // ping api first
      api.lpidata(filterParams).then((data) => {
        console.log('Getting data')
        console.log(data)
        data.map(function(currentValue) {
          if(+currentValue['count'] > 0) {
            that.dotPlotDataSet.datasets[0].data.push({ 'x': +currentValue['year'], 'y': +currentValue['ID'], 'r': 1 })
          } else if (+currentValue['count'] === 0) {
            that.dotPlotDataSet.datasets[1].data.push({ 'x': +currentValue['year'], 'y': +currentValue['ID'], 'r': 1 })
          }
        })
        that.dotPlot.update()
        that.loadingData = false
        // console.log(that.dotPlotDataSet)
      })
      // get files later
      var lpiResultFile = filtersStr + '/nesp_' + this.selectedYear.value + '_infile_Results.txt'
      console.log(lpiResultFile)
      api.lpiRunData(lpiResultFile, 'txt').then((data) => {
        // format:
        // 'LPI_final' 'CI_low' 'CI_low'
        // '1980' float float float
        that.lpiPlotDataSet.labels = []
        that.lpiPlotDataSet.datasets[0].data = []
        that.lpiPlotDataSet.datasets[1].data = []
        that.lpiPlotDataSet.datasets[1].data = []
        var lines = data.split('\n')
        // ignore first line
        lines = lines.slice(1)
        lines.map(function(currentValue) {
          if(currentValue.trim()) {
            var values = currentValue.split(' ')
            var year = values[0].replace(/"/g, '')
            if(values[1] !== 'NA' && values[2] !== 'NA' && values[3] !== 'NA') {
              that.lpiPlotDataSet.labels.push(parseInt(year))
              that.lpiPlotDataSet.datasets[0].data.push(parseFloat(values[1]))
              that.lpiPlotDataSet.datasets[1].data.push(parseFloat(values[2]))
              that.lpiPlotDataSet.datasets[2].data.push(parseFloat(values[3]))
            }
          }
        })
        console.log(that.lpiPlotDataSet)
        that.lpiPlot.update()
        // that.loadingData = false
      })
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
    },
    onYearSelect: function(aYear) {
      this.selectedYear = aYear
    }
  }
}
</script>

<style>
  .my-select {
    width: 240px;
  }
  .big-plot {
    width: 70% !important;
    height: 500px !important;;
  }
</style>
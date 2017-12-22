<template>
  <div class='plot content'>
    <h3 class='title'>NESP Plots</h3>
    <router-link to='/'>Back to imports</router-link>
    <hr>

    <table class='table is-fullwidth'>
      <thead>
        <tr>
          <th>Source</th>
          <th>Species</th>
          <th>Status</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <basic-select :options='sourceList' :selected-option='selectedSource' @select='onSourceSelect'>
            </basic-select>
          </td>
          
          <td>
            <basic-select :options='taxonList' :selected-option='selectedTaxon' @select='onTaxonSelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='statusList' :selected-option='selectedStatus' @select='onStatusSelect'>
            </basic-select>
          </td>

          <td>
            <basic-select :options='stateList' :selected-option='selectedState' @select='onStateSelect'>
            </basic-select>
          </td>
        </tr>
      </tbody>
    </table>

    <p>
      <button class='button is-primary' v-on:click='updatePlot' :disabled='loadingData'>Update</button>
    </p>
    <spinner size='large' message='Loading data....' v-show='loadingData'></spinner>
    <canvas ref='dotplot'></canvas>
    
  </div>
</template>
<script>
import * as api from '@/api'
import Chart from 'chart.js'
import Spinner from 'vue-simple-spinner'
import { BasicSelect } from 'vue-search-select'
// import * as util from '@/util'
export default {
  name: 'Plot',
  components: {
    Spinner, BasicSelect
  },
  data () {
    var data = {
      // taxon
      taxonList: [],
      selectedTaxon: {value: '0', text: 'All'},
      // source
      sourceList: [],
      selectedSource: {value: '0', text: 'All'},
      // status
      statusList: [],
      selectedStatus: {value: 'None', text: 'All'},
      // states
      stateList: [],
      selectedState: {value: 'None', text: 'All'},
      // chart
      chart: null,
      // chart data
      chartDataSet: null,
      // is loading dataset
      loadingData: false
    }
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
    // query data
    api.species().then((taxonList) => {
      data.taxonList = taxonList.map(i => { return {value: i['spno'], text: i['common_name']} })
      data.taxonList.push({value: 0, text: 'All'})
    })
    api.source().then((sourceList) => {
      data.sourceList = sourceList.map(i => { return {value: i['id'], text: i['description']} })
      data.sourceList.push({value: 0, text: 'All'})
    })
    api.status().then((statusList) => {
      data.statusList = statusList.map(i => { return {value: i['description'], text: i['description']} })
      data.statusList.push({value: 'None', text: 'All'})
    })
    return data
  },
  mounted: function() {
    this.chartDataSet = {
      animation: {
        duration: 10000
      },
      datasets: [{
        label: 'lpi yearly data',
        backgroundColor: '#4dc9f6',
        borderColor: 'black',
        borderWidth: 1,
        data: [] }]
    }
    var ctx = this.$refs.dotplot.getContext('2d')
    var that = this
    this.chart = new Chart(ctx, {
      type: 'bubble',
      data: that.chartDataSet,
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
  },
  methods: {
    updatePlot: function() {
      this.loadingData = true
      var filterParams = {}
      if (this.selectedTaxon.value !== '0') filterParams['spno'] = this.selectedTaxon.value
      if (this.selectedSource.value !== '0') filterParams['sourceid'] = this.selectedSource.value
      if (this.selectedState.value !== 'None') filterParams['state'] = this.selectedState.value
      if (this.selectedStatus.value !== 'None') filterParams['status'] = this.selectedStatus.value
      filterParams['format'] = 'dotplot'
      console.log(filterParams)
      var that = this
      api.lpidata(filterParams).then((data) => {
        // console.log('Getting data')
        that.chartDataSet.datasets[0].data = data.map(i => { return { 'x': +i['year'], 'y': +i['ID'], 'r': 1 } })
        that.chart.update()
        this.loadingData = false
        // console.log(that.chartDataSet)
      })
    }, // end updatePlot function
    onSourceSelect: function(aSource) {
      this.selectedSource = aSource
    }, // end onSourceSelect
    onTaxonSelect: function(aTaxon) {
      this.selectedTaxon = aTaxon
    }, // end onSourceSelect
    onStatusSelect: function(aStatus) {
      this.selectedStatus = aStatus
    }, // end onSourceSelect
    onStateSelect: function(aState) {
      this.selectedState = aState
    }
  }
}
</script>

<style>
  .my-select {
    width: 240px;
  }
</style>
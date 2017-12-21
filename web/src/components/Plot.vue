<template>
  <div class='plot content'>
    <h3 class='title'>NESP Plots</h3>
    <router-link to='/'>Back to imports</router-link>
    <hr>

    <table class='table is-fullwidth'>
      <thead>
        <tr>
          <th>Species</th>
          <th>Data Type</th>
          <th>Source</th>
          <th>Status</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <div class='select'>
              <select v-model=species class='my-select'>
                <option v-for='sp in speciesList' v-bind:value=sp.spno>{{sp.common_name}}</option>
              </select>
            </div>
          </td>

          <td>
            <div class='select'>
              <select v-model='dataType'>
                <option v-bind:value=0>None</option>
                <option v-bind:value=1>Type 1</option>
                <option v-bind:value=2>Type 2/3</option>
              </select>
            </div>
          </td>
          
          <td>
            <div class='select'>
              <select v-model=source class='my-select'>
                <option v-for='source in sourceList' v-bind:value=source.id>{{source.description}}</option>
              </select>
            </div>
          </td>
          
          <td>
            <div class='select'>
              <select v-model=status class='my-select'>
                <option v-for='status in statusList' v-bind:value=status.description>{{status.description}}</option>
              </select>
            </div>
          </td>


          <td>
            <div class='select'>
              <select v-model='state'>
                <option v-for='stateName in states' v-bind:value=stateName>{{stateName}}</option>
              </select>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <p>
      <button class='button is-primary' v-on:click='updatePlot'>Update</button>
    </p>

    <canvas ref='dotplot'></canvas>
    
  </div>
</template>
<script>
import * as api from '@/api'
import Chart from 'chart.js/dist/Chart.js'
// import * as util from '@/util'
// import Plotly from 'plotly.js/lib/core'
export default {
  name: 'Plot',
  props: ['groupBy', 'data'],
  data () {
    var data = {speciesList: [], sourceList: [], statusList: [], states: [], dataType: 0, species: 0, source: 0, status: 'None', region: 0, state: 'None', char: null, chartDataSet: null}
    // states filter
    data.states.push('None')
    data.states.push('Australian Capital Territory')
    data.states.push('Commonwealth')
    data.states.push('Queensland')
    data.states.push('New South Wales')
    data.states.push('Northern Territory')
    data.states.push('South Australia')
    data.states.push('Western Australia')
    data.states.push('Tasmania')
    data.states.push('Victoria')
    api.searchtype().then((searchlist) => {
      data.searchTypeList = searchlist
      data.searchTypeList.push({'id': 0, 'name': 'None'})
    })
    api.species().then((specieslist) => {
      data.speciesList = specieslist
      data.speciesList.push({'spno': 0, 'common_name': 'None'})
    })
    api.source().then((sourcelist) => {
      data.sourceList = sourcelist
      data.sourceList.push({'id': 0, 'description': 'None'})
    })
    api.status().then((statuslist) => {
      data.statusList = statuslist
      data.statusList.push({'id': 0, 'description': 'None'})
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
      var filterParams = {}
      if (this.dataType !== 0) filterParams['datatype'] = this.dataType
      if (this.species !== 0) filterParams['spno'] = this.species
      if (this.source !== 0) filterParams['sourceid'] = this.source
      if (this.state !== 'None') filterParams['state'] = this.state
      if (this.status !== 'None') filterParams['status'] = this.status
      filterParams['format'] = 'dotplot'
      console.log(filterParams)
      var that = this
      api.lpidata(filterParams).then((data) => {
        console.log('Getting data')
        that.chartDataSet.datasets[0].data = data.map(i => { return { 'x': +i['year'], 'y': +i['ID'], 'r': 1 } })
        that.chart.update()
        console.log(that.chartDataSet)
      })
    }// end updatePlot function
  }
}
</script>

<style>
  .my-select {
    width: 240px;
  }
</style>
<template>
  <div class='plot content'>
    <h3 class='title'>TSX Plots</h3>
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
    <canvas ref='lpiplot' class='medium-plot'></canvas>
    <canvas ref='intensityplot' class='medium-plot'></canvas>
    <canvas ref='dotplot' class='medium-plot'></canvas>
    <canvas ref='sumplot' class='medium-plot'></canvas>    
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
  name: 'TSX',
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
      // summayplot
      summaryPlotDataSet: null,
      summaryPlot: null,
      scatterChartData: null,
      loadingData: false,
      queryLPIData: true
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
    Chart.defaults.global.defaultFontSize = 30
    // ---------- dot plot -------------
    this.dotPlotDataSet = {
      datasets: [{
        label: 'count>0',
        backgroundColor: 'black',
        borderColor: 'black',
        borderWidth: 1,
        data: [] },
      {
        label: 'count==0',
        backgroundColor: 'grey',
        borderColor: 'grey',
        borderWidth: 1,
        data: [] }]
    }
    this.dotPlot = new Chart.Bubble(this.$refs.dotplot.getContext('2d'), {
      data: that.dotPlotDataSet,
      // Configuration options go here
      options: {
        responsive: true,
        tooltips: {
          mode: 'point'
        },
        scales: {
          yAxes: [{
            type: 'linear',
            display: true,
            position: 'left',
            scaleLabel: {
              display: true,
              labelString: 'Time series'
            }
          }]
        }
      }
    })
    // --------- summary plot ------------
    this.summaryPlotDataSet = {
      datasets: [{
        label: 'Species',
        xAxisID: 'x-axis-1',
        yAxisID: 'y-axis-1',
        borderColor: 'blue',
        backgroundColor: 'blue',
        data: []
      }, {
        label: 'TimesSeries',
        xAxisID: 'x-axis-1',
        yAxisID: 'y-axis-2',
        borderColor: 'red',
        backgroundColor: 'red',
        data: []
      }]
    }
    // --------- lpi plot ------------
    this.lpiPlotDataSet = {
      labels: [],
      datasets: [{
        label: 'TSX Final',
        borderColor: 'black',
        backgroundColor: 'black',
        fill: false,
        data: [] },
      {
        label: 'Confidence Interval (low)',
        borderColor: '#3e9555',
        backgroundColor: '#3e9555',
        fill: 1,
        data: [] },
      {
        label: 'Confidence Interval (high)',
        borderColor: '#3e95cd',
        backgroundColor: '#3e95cd',
        fill: 1,
        data: [] }]
    }
    this.lpiPlot = new Chart.Line(this.$refs.lpiplot.getContext('2d'), {
      data: that.lpiPlotDataSet,
      // Configuration options go here
      options: {
        responsive: true,
        scales: {
          yAxes: [{
            type: 'logarithmic',
            display: true,
            position: 'left',
            scaleLabel: {
              display: true,
              labelString: 'Index'
            },
            ticks: {
              min: 0.2,
              max: 2.0,
              callback: function(tick, index, ticks) {
                return tick.toLocaleString()
              }
            },
            gridLines: {
              drawOnChartArea: true
            }
          }]
        }
      }
    })
  },
  methods: {
    updatePlot: function() {
      console.log('Requery lpi data:' + this.queryLPIData)
      this.loadingData = true
      // clear existing data
      this.dotPlotDataSet.datasets[0].data = []
      this.dotPlotDataSet.datasets[1].data = []
      this.summaryPlotDataSet.datasets[0].data = []
      this.summaryPlotDataSet.datasets[1].data = []
      this.lpiPlotDataSet.labels = []
      this.lpiPlotDataSet.datasets[0].data = []
      this.lpiPlotDataSet.datasets[1].data = []
      this.lpiPlotDataSet.datasets[2].data = []
      // filters
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
      filterParams['format'] = 'plot'
      var that = this
      if(this.queryLPIData) {
        // ping api first
        api.lpidata(filterParams).then((data) => {
          // console.log('Getting data')
          // console.log(data)
          // dotplot
          var dotPlotData = data['dotplot']
          dotPlotData.map(function(currentValue) {
            if(+currentValue['count'] > 0) {
              that.dotPlotDataSet.datasets[0].data.push({ 'x': +currentValue['year'], 'y': +currentValue['ID'], 'r': 1 })
            } else if (+currentValue['count'] === 0) {
              that.dotPlotDataSet.datasets[1].data.push({ 'x': +currentValue['year'], 'y': +currentValue['ID'], 'r': 1 })
            }
          })
          // summary plot
          var speciesCountData = data['summary']['species']
          var timeSeriesCountData = data['summary']['timeseries']
          var year = 0
          for (year in speciesCountData) {
            that.summaryPlotDataSet.datasets[0].data.push({'x': +year, 'y': +speciesCountData[year]})
          }
          for (year in timeSeriesCountData) {
            that.summaryPlotDataSet.datasets[1].data.push({'x': +year, 'y': +timeSeriesCountData[year]})
          }
          // console.log(that.summaryPlotDataSet)
          that.dotPlot.update()
          // this will cause exception as the axis might be change
          // that.summaryPlot.update()
          that.refreshSummaryPlot()
          that.loadingData = false
          this.queryLPIData = false
        })
      }
      // get files later
      var lpiResultFile = filtersStr + '/nesp_' + this.selectedYear.value + '_infile_Results.txt'
      console.log(lpiResultFile)
      api.lpiRunData(lpiResultFile, 'txt').then((data) => {
        // format:
        // 'LPI_final' 'CI_low' 'CI_low'
        // '1980' float float float
        var lowestCI = 1.0
        var highestCI = 1.0
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
              var lowCIVal = parseFloat(values[2])
              that.lpiPlotDataSet.datasets[1].data.push(lowCIVal)
              if(lowCIVal < lowestCI) {
                lowestCI = lowCIVal
              }
              var highCIVal = parseFloat(values[3])
              that.lpiPlotDataSet.datasets[2].data.push(highCIVal)
              if(highCIVal > highestCI) {
                highestCI = highCIVal
              }
            }
          }
        })
        // update lpi plot
        that.lpiPlot.options.scales.yAxes[0].ticks.min = Number((lowestCI - 0.1).toFixed(1))
        that.lpiPlot.options.scales.yAxes[0].ticks.max = Number((highestCI + 0.1).toFixed(1))
        that.lpiPlot.update()
        if (!that.queryLPIData) {
          that.loadingData = false
        }
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
      this.queryLPIData = true
      this.loadingData = false
    }, // end onSourceSelect
    onSubGroupSelect: function(aSubGroup) {
      this.selectedSubGroup = aSubGroup
      this.queryLPIData = true
      this.loadingData = false
    }, // end onSourceSelect
    onStateSelect: function(aState) {
      this.selectedState = aState
      this.queryLPIData = true
      this.loadingData = false
    },
    onStatusAuthoritySelect: function(aStatusAuthority) {
      this.selectedStatusAuthority = aStatusAuthority
      if (this.selectedStatusAuthority.value === 'None') {
        this.selectedStatus = {value: 'None', text: 'All'}
        this.selectedStatusDisabled = true
        this.queryLPIData = true
        this.loadingData = false
      }
    }, // end onSourceSelect
    onStatusSelect: function(aStatus) {
      this.selectedStatus = aStatus
      this.queryLPIData = true
      this.loadingData = false
    },
    onYearSelect: function(aYear) {
      this.selectedYear = aYear
      this.loadingData = false
    },
    // refresh summary plot
    refreshSummaryPlot: function() {
      if (this.summaryPlot) {
        this.summaryPlot.destroy()
      }
      // create new one
      this.summaryPlot = new Chart.Scatter(this.$refs.sumplot.getContext('2d'), {
        data: this.summaryPlotDataSet,
        options: {
          responsive: true,
          hoverMode: 'nearest',
          intersect: true,
          title: {
            display: true,
            text: 'Data Summary'
          },
          scales: {
            xAxes: [{
              position: 'bottom',
              gridLines: {
                zeroLineColor: 'rgba(0,0,0,1)'
              }
            }],
            yAxes: [{
              type: 'linear',
              display: true,
              position: 'left',
              scaleLabel: {
                display: true,
                labelString: 'Number of taxa'
              },
              id: 'y-axis-1'
            }, {
              type: 'linear',
              display: true,
              position: 'right',
              reverse: true,
              id: 'y-axis-2',
              scaleLabel: {
                display: true,
                labelString: 'Number of time series'
              },
              // grid line settings
              gridLines: {
                drawOnChartArea: false
              }
            }]
          }
        }
      })
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
    height: 500px !important;
  }
  .medium-plot {
    width: 50% !important;
    height: 300px !important;
    float:left;
  }
</style>
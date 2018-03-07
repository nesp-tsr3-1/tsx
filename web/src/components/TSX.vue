<template>
  <div class='plot content'>
    <h3 class='title'>TSX Plots</h3>
    <router-link to='/'>Back to imports</router-link>

    <hr>

    <div class="tile is-ancestor">
      <div class="tile is-2 is-parent">
        <div class="tile is-child">
          <div class="field">
            <label class="label">Group</label>
            <div class="select is-fullwidth">
              <select v-model='selectedGroup' :disabled='prioritySelected'>
                <option v-for="option in groupList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">Sub-group</label>
            <div class="select is-fullwidth">
              <select v-model='selectedSubGroup' :disabled='prioritySelected'>
                <option v-for="option in subGroupList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">State</label>
            <div class="select is-fullwidth">
              <select v-model='selectedState' :disabled='prioritySelected'>
                <option v-for="option in stateList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">Status authority</label>
            <div class="select is-fullwidth">
              <select v-model='selectedStatusAuthority' :disabled='prioritySelected'>
                <option v-for="option in statusAuthorityList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">Status</label>
            <div class="select is-fullwidth">
              <select v-model='selectedStatus' :disabled='prioritySelected'>
                <option v-for="option in statusList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">Reference year</label>
            <div class="select is-fullwidth">
              <select v-model='selectedYear'>
                <option v-for="option in yearList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          
          <div class="field">
            <input type="checkbox" id="checkbox" v-model="prioritySelected">
            <label for="checkbox">Priority Group</label>
          </div>

          <p>
            <button class='button is-primary' v-on:click='downloadCSV'>Download CSV</button>
          </p>
          <p>
            <button class='button is-primary' v-on:click='viewDataSummary'>Data Summary</button>
          </p>
        </div>
      </div>

      <div class="modal is-active" v-show='loadingData && !showFullMap'>
        <div class="modal-background"></div>
        <div class="modal-card">
          <section class="modal-card-body">
            <spinner size='large' message='Loading data....'></spinner>
          </section>
        </div>
      </div>

      <div class="tile is-vertical" v-show="!noData">
        <div class="tile">
          <div class="tile is-parent is-vertical" v-show="!showFullMap">
            <div class="tile is-child card">
                <canvas ref='lpiplot'></canvas>
            </div>
            <div class="tile is-child card">
                <canvas ref='dotplot'></canvas>
            </div>
          </div>
          <div class="tile is-parent is-vertical">
            <div class="tile is-child card">
              <vue-slider ref='slider' v-bind='sliderData' v-model='sliderRange' class='heatmap-slider'></vue-slider>
              <div id='intensityplot' ref='intensityplot' class='heatmap-div'></div>
              <spinner size='large' message='Loading map....' v-show='loadingMap' class='heatmap-spinner'></spinner>
            </div>
            <div class="tile is-child card" v-show="!showFullMap">
              <canvas ref='sumplot'></canvas>
            </div>
            
          </div>
        </div>
      </div>

      <div class="tile is-child" v-show="noData">
        <p style="margin: 0.8em">(No data to show)</p>
      </div>
    </div>
  </div>
</template>
<script>
import * as api from '@/api'
import Chart from 'chart.js'
import Spinner from 'vue-simple-spinner'
import L from 'leaflet'
import HeatmapOverlay from 'heatmap.js/plugins/leaflet-heatmap/leaflet-heatmap.js'
import easyButton from 'leaflet-easybutton/src/easy-button.js'
import vueSlider from 'vue-slider-component/dist/index.js'
export default {
  name: 'TSX',
  components: {
    Spinner, easyButton, vueSlider
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
      // charts
      dotPlot: null,
      dotPlotDataSet: null,
      // lpi plot
      lpiPlot: null,
      lpiPlotDataSet: null,
      // summayplot
      summaryPlotDataSet: null,
      summaryPlot: null,
      // is loading data
      loadingData: false,
      // need to query LPI rest service
      queryLPIData: true,
      // no data to show
      noData: true,
      // prioritySelected
      prioritySelected: false,
      // heatmap
      // intensity plot
      loadingMap: false,
      heatmapLayer: null,
      // this stores the data from the API, heatmapDataSet.data contains subset of it
      surveyData: [],
      heatmapDataSet: {max: 0, min: 0, data: []},
      map: null,
      showFullMap: false,
      sliderRange: [1960, 2017],
      sliderData: {
        eventType: 'auto',
        width: 'auto',
        height: 4,
        dotSize: 14,
        min: 1960,
        max: 2020,
        interval: 1,
        disabled: false,
        show: false,
        lazy: true,
        tooltip: 'always'
      }
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
    data.statusList.push({value: 'Near Threatened', text: 'Near Threatened'})
    data.statusList.push({value: 'Vulnerable', text: 'Vulnerable'})
    data.statusList.push({value: 'Endangered', text: 'Endangered'})
    data.statusList.push({value: 'Critically Endangered', text: 'Critically Endangered'})
    return data
  },
  mounted: function() {
    var that = this
    Chart.defaults.global.defaultFontSize = 14
    // ---------- dot plot -------------
    this.dotPlotDataSet = {
      datasets: [{
        label: 'count > 0',
        backgroundColor: 'black',
        borderColor: 'black',
        borderWidth: 1,
        data: [] },
      {
        label: 'count = 0',
        backgroundColor: 'grey',
        borderColor: 'grey',
        borderWidth: 1,
        data: [] }]
    }
    this.dotPlot = new Chart.Bubble(this.$refs.dotplot.getContext('2d'), {
      data: that.dotPlotDataSet,
      // Configuration options go here
      options: {
        animation: false,
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
          }],
          xAxes: [{
            type: 'linear',
            ticks: {
              min: 1950,
              max: 2020
            }
          }]
        }
      }
    })
    // --------- summary plot ------------
    this.summaryPlotDataSet = {
      datasets: [{
        label: 'Number of taxa',
        xAxisID: 'x-axis-1',
        yAxisID: 'y-axis-1',
        borderColor: 'blue',
        backgroundColor: 'blue',
        data: []
      }, {
        label: 'Number of time series',
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
        label: 'TSX',
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

    // -------intensity plot ----------------
    var baseLayer = L.tileLayer(
      'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    // TODO: might need to tweak some of these
    var cfg = {
      'fullscreenControl': true,
      'radius': 0.45,
      'maxOpacity': 0.8,
      'minOpacity': 0.5,
      'blur': 0.75,
      'scaleRadius': true,
      'useLocalExtrema': false,
      latField: 'lat',
      lngField: 'long',
      valueField: 'count',
      gradient: {0.25: 'rgb(0,94,255)', 0.5: 'rgb(0,0,255)', 0.85: 'rgb(163,0,255)', 1.0: 'rgb(255,0,255)'}
    }
    this.heatmapLayer = new HeatmapOverlay(cfg)
    this.map = new L.Map('intensityplot', {
      center: new L.LatLng(-20.917574, 142.702789),
      zoom: 4,
      layers: [baseLayer, this.heatmapLayer]
    })
    // /////////// map control /////////////////////////
    // setupbutton
    L.easyButton('<strong>&#9881;</strong>', function(buttonArg, mapArg) {
      // do stuff
      console.log('show settings')
    },
    { position: 'bottomleft' }).addTo(that.map)
    L.easyButton({
      id: 'expand',
      position: 'bottomleft',
      states: [{
        icon: '<strong>&swarr;</strong>',
        stateName: 'small',
        onClick: function(btn, map) {
          btn.state('big')
          that.showFullMap = true
          // this is to make the slider properlly align with the resize event
          that.sliderData.max = that.sliderData.max + 1
          setTimeout(function() {
            that.map.invalidateSize()
            that.sliderData.max = that.sliderData.max - 1
          }, 500)
        }
      }, {
        icon: '<strong>&nearr;</strong>',
        stateName: 'big',
        onClick: function(btn, map) {
          btn.state('small')
          that.showFullMap = false
          that.sliderData.max = that.sliderData.max + 1
          setTimeout(function() {
            that.map.invalidateSize()
            that.sliderData.max = that.sliderData.max - 1
          }, 2000)
        }
      }]
    }).addTo(that.map)
    //
    // this is a hack so that leaflet displays properlly
    setTimeout(function() {
      that.map.invalidateSize()
      console.log('---update plot----')
    }, 2000)
    this.updatePlot()
  },
  watch: {
    selectedGroup(val) {
      if(val.value === 'None') {
        this.selectedSubGroupDisabled = true
        this.selectedSubGroup = {value: 'None', text: 'All'}
      }
    },
    selectedStatusAuthority(val) {
      if(val.value === 'None') {
        this.selectedStatusDisabled = true
        this.selectedStatus = {value: 'None', text: 'All'}
      }
    },
    filterParams(val, oldVal) {
      this.queryLPIData = true
      this.loadingData = false
      this.updatePlot()
    },
    selectedYear(val) {
      this.updatePlot()
    },
    sliderRange(range) {
      if(this.loadingMap) {
        return
      }
      var that = this
      var minYear = range[0]
      var maxYear = range[1]
      that.heatmapDataSet.data = []
      // color scale ramains the same
      // var countMin = 10000
      // var countMax = 0
      that.surveyData.forEach(function(element) {
        if(element['year'] >= minYear && element['year'] <= maxYear) {
          that.heatmapDataSet.data.push(element)
          // if (element['count'] > countMax) countMax = element['count']
          // if (element['count'] < countMin) countMin = element['count']
        }
      })
      // that.heatmapDataSet.min = countMin
      // that.heatmapDataSet.max = countMax
      that.heatmapLayer.setData(that.heatmapDataSet)
      that.map.invalidateSize()
    }
  },
  computed: {
    filterParams() {
      return this.getFilterParams()
    }
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
      this.heatmapDataSet.data = []
      this.surveyData = []
      // filters
      var filtersStr = this.getFilterString()
      var filterParams = this.getFilterParams()
      filterParams['format'] = 'plot'
      var that = this
      if(this.queryLPIData) {
        // ping api first
        api.lpiPlot(filterParams).then((data) => {
          this.noData = data['dotplot'].length === 0

          // console.log('Getting data')
          // console.log(data)
          // dotplot
          var dotPlotData = data['dotplot']

          dotPlotData.forEach(function(timeSeries, i) {
            timeSeries.forEach(function(value) {
              var year = value[0]
              var count = value[1]
              that.dotPlotDataSet.datasets[count === 0 ? 1 : 0].data.push({
                x: year,
                y: i + 1,
                r: 1
              })
            })
          })
          // summary plot
          // var speciesCountData = data['summary']['species']
          var taxaCountData = data['summary']['taxa']
          var timeSeriesCountData = data['summary']['timeseries']
          var year = 0
          for (year in taxaCountData) {
            that.summaryPlotDataSet.datasets[0].data.push({'x': +year, 'y': +taxaCountData[year]})
          }
          for (year in timeSeriesCountData) {
            that.summaryPlotDataSet.datasets[1].data.push({'x': +year, 'y': +timeSeriesCountData[year]})
          }
          that.dotPlot.update()
          // this will cause exception as the axis might be change
          // that.summaryPlot.update()
          that.refreshSummaryPlot()
        }).finally(() => {
          that.queryLPIData = false
          that.loadingData = false
        })
      }
      // intensity plot
      that.loadingMap = true
      this.sliderData.show = false
      api.intensityPlot(filterParams).then((data) => {
        console.log('--loading map data----')
        var yearMin = 30000 // we should be in mars by then
        var yearMax = 1000
        var countMin = 10000
        var countMax = 0
        data.forEach(function(timeSerie) {
          var lat = timeSerie[1]
          var long = timeSerie[0]
          var yearCount = timeSerie[2]
          yearCount.forEach(function(element) {
            that.surveyData.push({
              'lat': lat,
              'long': long,
              'count': element[1],
              'year': element[0]
            })
            if (element[1] > countMax) countMax = element[1]
            if (element[1] < countMin) countMin = element[1]
            if (element[0] < yearMin) yearMin = element[0]
            if (element[0] > yearMax) yearMax = element[0]
          })
        })
        that.sliderData.min = yearMin
        that.sliderData.max = yearMax
        that.heatmapDataSet.max = countMax
        that.heatmapDataSet.min = countMin
        that.sliderRange = [that.sliderData.min, that.sliderData.max]
        that.heatmapDataSet.data = that.surveyData
        that.heatmapLayer.setData(that.heatmapDataSet)
        that.map.invalidateSize()
      }).finally(() => {
        that.loadingMap = false
        that.sliderData.show = true
      })
      // get files later
      var lpiResultFile = filtersStr + '/nesp_' + this.selectedYear.value + '_infile_Results.txt'
      console.log(lpiResultFile)
      api.lpiRunData(lpiResultFile, 'txt').then((data) => {
        if(data) {
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
        }
      }).finally(() => {
        if (!that.queryLPIData) {
          that.loadingData = false
        }
      })
    }, // end updatePlot function
    downloadCSV: function() {
      var filterParams = this.getFilterParams()
      filterParams['format'] = 'csv'
      filterParams['download'] = 'widetable.csv'
      var url = api.lpiDownloadURL(filterParams)
      window.open(url)
    },
    viewDataSummary: function() {
      var filterParams = this.getFilterParams()
      var url = api.lpiSummaryURL(filterParams)
      window.open(url)
    },
    getFilterParams: function() {
      var filterParams = {}
      if(this.prioritySelected) {
        filterParams['priority'] = 1
      } else {
        if(this.selectedGroup.value !== 'None') {
          filterParams['group'] = this.selectedGroup.value
        }
        if(this.selectedSubGroup.value !== 'None') {
          filterParams['subgroup'] = this.selectedSubGroup.value
        }
        if(this.selectedState.value !== 'None') {
          filterParams['state'] = this.selectedState.value
        }
        if(this.selectedStatusAuthority.value !== 'None') {
          filterParams['statusauth'] = this.selectedStatusAuthority.value
        }
        if(this.selectedStatus.value !== 'None') {
          filterParams['status'] = this.selectedStatus.value
        }
      }
      return filterParams
    },
    getFilterString: function() {
      var filtersStr = ''
      if(this.prioritySelected) {
        filtersStr = 'priority-1'
      } else {
        if(this.selectedGroup.value !== 'None') {
          filtersStr = filtersStr + 'group-' + this.selectedGroup.value + '_'
        }
        if(this.selectedSubGroup.value !== 'None') {
          filtersStr = filtersStr + 'subgroup-' + this.selectedSubGroup.value + '_'
        }
        if(this.selectedState.value !== 'None') {
          filtersStr = filtersStr + 'state-' + this.selectedState.value + '_'
        }
        if(this.selectedStatusAuthority.value !== 'None') {
          filtersStr = filtersStr + 'statusauth-' + this.selectedStatusAuthority.value + '_'
        }
        if(this.selectedStatus.value !== 'None') {
          filtersStr = filtersStr + 'status-' + this.selectedStatus.value
        }
      }
      return filtersStr
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
          // title: {
          //   display: true,
          //   text: 'Data Summary'
          // },
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

<style src='leaflet/dist/leaflet.css'>
</style>
<style src='leaflet-easybutton/src/easy-button.css'>
</style>
<style>
  .heatmap-div {
    width: 100%;
    height: 100%;
    z-index:1;
  }
  .heatmap-spinner{
    z-index:2;
    position:absolute;
    top:0;
    bottom:0;
    left:0;
    right:0;
  }
  .heatmap-slider{
    z-index:2;
    width: 100%;
    height: 16px;
    position:absolute !important;
    top:0;
    bottom:0;
    left:0;
    right:0;
  }
</style>

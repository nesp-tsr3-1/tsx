<template>
  <div class="section is-dark" style="padding-bottom: 1em;">
    <div class="container is-widescreen">

  <div class='plot content'>
    <div class="tile is-ancestor">
      <div class="tile is-2 is-parent">
        <div class="tile is-child">
          <div class="field">
            <label class="label">Index</label>
            <div class="select is-fullwidth">
              <select v-model='selectedIndex' :disabled='prioritySelected'>
                <option v-for="option in indexList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
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
              <select v-model='selectedSubgroup' :disabled='prioritySelected || !subgroupEnabled'>
                <option v-for="option in subgroupList" v-bind:value="option">{{option.text}}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label class="label">State / Territory</label>
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
            <input type="checkbox" id="checkbox" v-model="prioritySelected">
            <label for="checkbox"> National priority species</label>
          </div>

          <hr>

          <div class="field" v-if='managementEnabled'>
            <label class="label">Management</label>
            <div class="select is-fullwidth">
              <select v-model='selectedManagement'>
                <option v-for="option in managementList" v-bind:value="option">{{option.text}}</option>
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


          <p>
            <button class='button is-primary is-small' v-on:click='downloadCSV'>Download CSV</button>
          </p>
          <p>
            <button class='button is-primary is-small' v-on:click='downloadTrend' :disabled='trendData == null'>Download Trend</button>
          </p>
          <p>
            <button class='button is-primary is-small' v-on:click='viewDataSummary'>Data Summary</button>
          </p>
        </div>
      </div>

      <div class="modal is-active" v-show='loadingData && !showFullMap'>
        <div class="modal-background" style="background: rgba(0,0,0,0.2)"></div>
        <div class="modal-card">
          <section class="modal-card-body">
            <spinner size='large' message='Loading data....'></spinner>
          </section>
        </div>
      </div>

      <div class="tile is-vertical ie11-bugfix" v-show="!noData">
        <div class="tile">
          <div class="tile is-parent is-vertical" v-show="!showFullMap">
            <div class="tile is-child card">
              <h4 class="has-text-black">Main index</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                      <p>The index shows the average change in populations compared to a base year. It shows a relative change and not population numbers themselves. At the reference year, the index gets an index score of one. A score of 1.2 would mean a 20% increase on average compared to the reference year, while a score of 0.8 would mean a 20% decrease on average compared to the reference year.</p>
                      <p>Check this index:</p>
                      <ol>
                        <li>Look at <b>Spatial representativeness</b> map to see how much data there are and where these data come from.</li>
                        <li>Look at <b>Monitoring consistency</b> to see how consistently each monitoring location was visited over time.</li>
                        <li>Go to <b>Time series and species accumulation</b> plot to see how many time series and species/subspecies were used to calculate this index in each year</li>
                        <li>Adjust the <b>Reference year</b> to let the index start at a year with more data</li>
                        <li>Go to <b>Data Summary</b> to see which species/subspecies were included in this index</li>
                        <li>Go to <b>Download CSV</b> to get the aggregated data used to calculate this index.</li>
                      </ol>
                  </div>
                </template>
              </tippy>
              <div class="plot-container" v-show="!noLPI">
                <canvas ref='lpiplot'></canvas>
              </div>
              <div class="has-text-black" v-show="noLPI">
                <p>No index generated – less than 3 taxa present at the selected reference year.</p>
                <p>Try changing the reference year to build an index</p>
              </div>
            </div>
            <div class="tile is-child card">
              <h4 class="has-text-black">Monitoring consistency</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This dot plot shows the particular years for which monitoring data were available. Each row represents a time series where a species/subspecies was monitored with a consistent method at a single site. The dots represent count values for the metric used to quantify the species/subspecies while zeros indicate absences (non-detections) of those species at the site.
                  </div>
                </template>
              </tippy>
              <div class="plot-container">
                <canvas ref='dotplot'></canvas>
              </div>
            </div>
          </div>
          <div class="tile is-parent is-vertical">
            <div class="tile is-child card map-tile">
              <h4 class="has-text-black">Spatial representativeness</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This map shows where threatened species data to calculate this index are recorded in Australia. Light blue indicates less data (fewer sites monitored), pink indicates more data (more sites monitored).
                  </div>
                </template>
              </tippy>
              <div id='intensityplot' ref='intensityplot' class='heatmap-div'></div>
              <spinner size='medium' v-show='loadingMap' class='heatmap-spinner'></spinner>
            </div>
            <div class="tile is-child card" v-show="!showFullMap">
              <h4 class="has-text-black">Number of time series and species per year</h4>
              <tippy class="info-icon icon" arrow interactive placement="left">
                <template #default><i class="far fa-question-circle"></i></template>
                <template #content>
                  <div class="popup-content">
                    This plot shows the number of species/subspecies (in blue) and the number of time series (in green) available in each year to calculate the index.
                  </div>
                </template>
              </tippy>
              <div class="plot-container">
                <canvas ref='sumplot'></canvas>
              </div>
            </div>

          </div>
        </div>
      </div>

      <div class="tile is-child" v-show="noData">
        <p style="margin: 0.8em">(No data to show)</p>
      </div>
    </div>

    <!-- warning dialog -->
    <div class="modal is-active" v-show="!hasAcceptedWarning">
      <div class="modal-background"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <span class="modal-card-title">Caution</span>
        </header>
        <section class="modal-card-body" style="color:black">
          <p>This page presents preliminary trends for the 2022 compilation of the Threatened Species Index, for consultation purposes. These trends may change following review by key stakeholders, which will be finalised in early 2023.</p>
          <p>Please also consider that the trends produced by this tool vary in their reliability. While the TSX team implements rigorous data quality standards, a trend is ultimately only as good as the underlying data.</p>
          <p>We have developed diagnostic tools to help assess the reliability of each trend. <a target="_blank" rel="noopener noreferrer" href="https://tsx.org.au/visualising-the-index/how-good/">(Click here for more details on how to assess reliability of trends)</a></p>
          <p>By using this tool you acknowledge the preliminary nature of these trends and the precautions regarding trend generation and reliability.</p>
        </section>
        <footer class="modal-card-foot">
          <button class="button" v-on:click='acceptWarning'>I Accept</button>
          <button class="button" v-on:click='goBack'>Cancel</button>
        </footer>
      </div>
    </div>
  </div>

    </div>
  </div>
</template>
<script>
import * as api from '../api.js'
import {
  Chart,
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
} from 'chart.js'

Chart.register(
  LineElement,
  PointElement,
  BubbleController,
  LineController,
  ScatterController,
  CategoryScale,
  LinearScale,
  TimeScale,
  TimeSeriesScale,
  Filler,
  Legend,
  Title,
  Tooltip,
  SubTitle
)

import Spinner from 'vue-simple-spinner/src/components/Spinner.vue'
import L from 'leaflet'
import HeatmapOverlay from 'heatmap.js/plugins/leaflet-heatmap/leaflet-heatmap.js'
import 'leaflet-easybutton/src/easy-button.js'
import { min, max, pluck, uniq, parseParams, encodeParams } from '../util.js'
import { Tippy } from 'vue-tippy'

// Generated with:
// SELECT REPLACE(REPLACE(JSON_ARRAYAGG(o), """", "'"), "], ", "],\n") FROM (SELECT DISTINCT JSON_ARRAY(taxonomic_group, group_name, subgroup_name) AS o FROM taxon JOIN taxon_group ON taxon.id = taxon_id ORDER BY taxonomic_group, group_name, subgroup_name) t\G

// Note: Have manually commented out combinations without enough time series to make a trend. TODO - make this automated somehow.

const groupings = [
  ['Birds', 'Marine', null],
  ['Birds', 'Marine', 'Albatrosses and Giant-Petrels'],
  // ['Birds', 'Marine', 'Gulls Terns Noddies Skuas Jaegers'],
  // ['Birds', 'Marine', 'Penguins'],
  // ['Birds', 'Marine', 'Petrels and Shearwaters'],
  // ['Birds', 'Marine', 'Tropicbirds Frigatebirds Gannets Boobies'],
  ['Birds', 'Shoreline (migratory)', null],
  // ['Birds', 'Shoreline (resident)', null],
  ['Birds', 'Terrestrial', null],
  // ['Birds', 'Terrestrial', 'Arid Woodland/ shrubland'],
  ['Birds', 'Terrestrial', 'Dry sclerophyll woodland/forest'],
  // ['Birds', 'Terrestrial', 'Grassland'],
  // ['Birds', 'Terrestrial', 'Heathland'],
  // ['Birds', 'Terrestrial', 'Island endemic'],
  // ['Birds', 'Terrestrial', 'Mallee woodland'],
  // ['Birds', 'Terrestrial', 'Parrots Lorikeets Rosellas Cockatoos Corellas'],
  // ['Birds', 'Terrestrial', 'Rainforest'],
  ['Birds', 'Terrestrial', 'Tropical savanna woodland'],
  // ['Birds', 'Wetland', null],
  // ['Birds', 'Wetland', 'Gulls Terns Noddies Skuas Jaegers'],
  ['Mammals', '<50g', null],
  ['Mammals', '50-5000g', null],
  ['Mammals', '>5000g', null],
  ['Mammals', 'Marine', null],
  ['Mammals', 'Terrestrial', null],
  ['Mammals', 'Terrestrial', 'Arboreal'],
  ['Mammals', 'Terrestrial', 'Volant'],
  // ['Plants', 'Grass', null],
  ['Plants', 'Herbaceous', null],
  ['Plants', 'Orchid', null],
  ['Plants', 'Shrub', null],
  ['Plants', 'Tree', null],
  // ['Plants', 'Terrestrial', null]
]

const noneOption = {value: 'None', text: 'All'}

function generateIndexList() {
  let indexList = uniq(groupings.map(x => x[0]))

  return [noneOption].concat(indexList.map(x => ({value: x, text: x})))
}

function generateGroupList(index) {
  var groupList
  if(index.value === 'None') {
    groupList = ['Marine', 'Terrestrial']
  } else {
    groupList = uniq(groupings.filter(x => index.value === x[0]).map(x => x[1]))
  }

  return [noneOption].concat(groupList.map(x => ({value: x, text: x})))
}

function generateSubgroupList(index, group) {
  var subgroupList
  if(index.value === 'None' || group.value === 'None') {
    subgroupList = []
  } else {
    subgroupList = uniq(groupings.filter(x => index.value === x[0] && group.value === x[1] && x[2] !== null).map(x => x[2]))
  }

  return [noneOption].concat(subgroupList.map(x => ({value: x, text: x})))
}

const states = [
  {value: 'None', text: 'All', shortValue: null},
  {value: 'Australian Capital Territory', text: 'Australian Capital Territory', shortValue: "ACT"},
  // {value: 'Commonwealth', text: 'Commonwealth'},
  {value: 'Queensland', text: 'Queensland', shortValue: "QLD"},
  {value: 'New South Wales', text: 'New South Wales', shortValue: "NSW"},
  {value: 'Australian Capital Territory+New South Wales', text: 'Australian Capital Territory + New South Wales', shortValue: "ACT,NSW"},
  {value: 'Northern Territory', text: 'Northern Territory', shortValue: "NT"},
  {value: 'South Australia', text: 'South Australia', shortValue: "SA"},
  {value: 'Western Australia', text: 'Western Australia', shortValue: "WA"},
  {value: 'Tasmania', text: 'Tasmania', shortValue: "TAS"},
  {value: 'Victoria', text: 'Victoria', shortValue: "VIC"}
]

const statusAuthorities = [
  {value: 'Max', text: 'Max'},
  {value: 'EPBC', text: 'EPBC'},
  {value: 'IUCN', text: 'Australian IUCN status'},
  {value: 'BirdActionPlan', text:'2020 Bird Action Plan'}
]

const statuses = [
  {
    shortValue: 'VU_EN_CR',
    value: 'Vulnerable+Endangered+Critically Endangered',
    text: 'Threatened species (all Vulnerable + Endangered + Critically Endangered)'
  }, {
    shortValue: 'NT_VU_EN_CR',
    value: 'Near Threatened+Vulnerable+Endangered+Critically Endangered',
    text: 'All (all Near Threatened + Vulnerable + Endangered + Critically Endangered)'
  }, {
    shortValue: 'NT',
    value: 'Near Threatened',
    text: 'Near Threatened species (Near Threatened species only)'
  }
]

const managementTypes = [
  { value: 'None', text: 'All sites', groups: ['Mammals', 'Plants'] },
  { value: 'Actively managed', text: 'Actively managed', groups: ['Mammals', 'Plants'] },
  { value: 'No known management', text: 'No known management', groups: ['Mammals', 'Plants'] }
]

const years = [
  {value: '1985', text: '1985'},
  {value: '1990', text: '1990'},
  {value: '1995', text: '1995'},
  {value: '2000', text: '2000'}
]

export default {
  name: 'TSX',
  components: {
    Spinner,
    Tippy
  },
  data () {
    var data = {
      // index
      indexList: generateIndexList(),
      selectedIndex: noneOption,
      // group
      groupList: generateGroupList(noneOption),
      selectedGroup: noneOption,
      // subgroup
      subgroupList: generateSubgroupList(noneOption, noneOption),
      selectedSubgroup: noneOption,
      subgroupEnabled: false,
      // states
      stateList: states,
      selectedState: states[0],
      // status auth
      statusAuthorityList: statusAuthorities,
      selectedStatusAuthority: statusAuthorities[0],
      // status
      statusList: statuses,
      selectedStatus: statuses[1],
      // management
      managementList: managementTypes,
      selectedManagement: managementTypes[0],

      // year
      yearList: years,
      selectedYear: years[0],
      // charts

      // is loading data
      loadingData: false,
      // no data to show
      noData: true,
      // no LPI run to show
      noLPI: false,
      // prioritySelected
      prioritySelected: false,
      // heatmap
      // intensity plot
      loadingMap: false,
      // heatmapLayer: null,
      trendData: null,

      // map: null,
      showFullMap: false,
      hasAcceptedWarning: localStorage.getItem('hasAcceptedWarning') || false
    }

    return data
  },
  mounted: function() {
    Chart.defaults.font.size = 14
    this.createMonitoringConsistencyPlot()
    this.createSummaryPlot()
    this.createMainIndexPlot()

    // -------intensity plot ----------------
    var baseLayer = L.tileLayer(
      '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    this.heatmapLayer = new HeatmapOverlay({
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
    })
    this.map = new L.Map('intensityplot', {
      center: new L.LatLng(-25.917574, 132.702789),
      zoom: 3,
      layers: [baseLayer, this.heatmapLayer]
    })
    // /////////// map control /////////////////////////

    L.easyButton({
      id: 'expand',
      position: 'bottomleft',
      states: [{
        icon: '<strong style="color: black">&swarr;</strong>',
        stateName: 'small',
        onClick: (btn, map) => {
          btn.state('big')
          this.showFullMap = true
          setTimeout(function() { window.dispatchEvent(new Event('resize')) })
        }
      }, {
        icon: '<strong style="color: black">&nearr;</strong>',
        stateName: 'big',
        onClick: (btn, map) => {
          btn.state('small')
          this.showFullMap = false
          setTimeout(function() { window.dispatchEvent(new Event('resize')) })
        }
      }]
    }).addTo(this.map)
    //
    // this is a hack so that leaflet displays properlly
    setTimeout(() => {
      this.map.invalidateSize()
      console.log('---update plot----')
    }, 2000)
    this.updateMapAndPlots()

    this.updateFromQueryString()
  },
  watch: {
    selectedIndex(val) {
      this.groupList = generateGroupList(this.selectedIndex)
      this.groupEnabled = this.subgroupList.length > 1

      this.selectedGroup = this.groupList.find(x => x.value === this.selectedGroup.value) || this.groupList[0]

      this.subgroupList = generateSubgroupList(this.selectedIndex, this.selectedGroup)
      this.subgroupEnabled = this.subgroupList.length > 1

      this.selectedSubgroup = this.subgroupList.find(x => x.value === this.selectedSubgroup.value) || this.subgroupList[0]

      this.updateStatusAuthorityList()
      this.updateManagementList()
    },
    prioritySelected(val) {
      this.updateStatusAuthorityList()
      this.updateManagementList()
    },
    selectedGroup(val) {
      this.subgroupList = generateSubgroupList(this.selectedIndex, this.selectedGroup)
      this.subgroupEnabled = this.subgroupList.length > 1

      this.selectedSubgroup = this.subgroupList.find(x => x.value === this.selectedSubgroup.value) || this.subgroupList[0]
    },
    selectedStatusAuthority(val) {
      if(val.value === 'None') {
        this.selectedStatusDisabled = true
        this.selectedStatus = {value: 'None', text: 'All'}
      }
    },
    filterParams(val, oldVal) {
      this.updateMapAndPlots()
    },
    filterQueryString(val) {
      var url = window.location.pathname
      if(val) {
        url += '?' + val
      }
      history.replaceState(null, '', url)
    }
  },
  computed: {
    filterParams() {
      return this.getFilterParams()
    },
    filterQueryString() {
      var params = {
        ref: this.selectedYear.value
      }

      function addParam(key, selectedItem) {
        if(selectedItem.value !== 'None') {
          params[key] = selectedItem.shortValue || selectedItem.value
        }
      }

      if(this.prioritySelected) {
        params['priority'] = '1'
      } else {
        addParam('index', this.selectedIndex)
        addParam('group', this.selectedGroup)
        addParam('subgroup', this.selectedSubgroup)
        addParam('state', this.selectedState)
        addParam('status_auth', this.selectedStatusAuthority)
        addParam('status', this.selectedStatus)
      }

      if(this.managementEnabled) {
        addParam('management', this.selectedManagement)
      }

      return Object.entries(params).map(x => x[0] + '=' + encodeURIComponent(x[1])).join("&")
    },
    filterFilenamePart() {
      var filterParams = this.getFilterParams()
      var name = decodeURIComponent(this.filterQueryString).replace(/[<>:"/\\|?*]/g, '-')
      if(filterParams.dataset) {
        name = "dataset=" + filterParams.dataset + "&" + name
      }
      return name
    },
    managementEnabled() {
      return this.selectedIndex.value === 'Mammals' || this.selectedIndex.value === 'Plants' || this.prioritySelected
    },
    downloadTrendURL() {
      if(this.trendData) {
        return "data:text/plain," + encodeURIComponent(this.trendData)
      } else {
        return ""
      }
    }
  },
  methods: {
    updateFromQueryString() {
      console.log("updateFromQueryString")
      var params = parseParams(window.location.search.substr(1))

      var self = this
      function updateFromParam(key, valueKey, list) {
        if(params[key]) {
          var value = list.filter(x => x.shortValue == params[key] || x.value == params[key])[0]
          console.log("key = " + key + ", value = " + value)
          self[valueKey] = value
        }
      }

      updateFromParam('ref', 'selectedYear', this.yearList)
      updateFromParam('index', 'selectedIndex', this.indexList)
      updateFromParam('group', 'selectedGroup', this.groupList)
      updateFromParam('state', 'selectedState', this.stateList)
      updateFromParam('status_auth', 'selectedStatusAuthority', this.statusAuthorityList)
      updateFromParam('status', 'selectedStatus', this.statusList)
      updateFromParam('management', 'selectedManagement', this.managementList)
    },
    updateManagementList() {
      if(this.managementEnabled) {
        this.managementList = managementTypes
      } else {
        this.managementList = []
      }
    },
    updateStatusAuthorityList() {
      if(this.prioritySelected || this.selectedIndex.value === 'Birds' || this.selectedIndex.value === 'None') {
        this.statusAuthorityList = statusAuthorities
      } else {
        this.statusAuthorityList = statusAuthorities.filter(x => x.value != 'BirdActionPlan')
      }
      if(!this.statusAuthorityList.includes(this.selectedStatusAuthority)) {
        this.selectedStatusAuthority = this.statusAuthorityList[0];
      }
    },
    createMainIndexPlot() {
      var data = {
        labels: [],
        datasets: [{
          label: 'TSX',
          borderColor: '#36699e',
          backgroundColor: 'black',
          fill: false,
          pointRadius: 0,
          lineTension: 0,
          data: []
        }, {
          label: 'Confidence Interval (low)',
          backgroundColor: 'rgba(230,230,230,0.5)',
          fill: false,
          pointRadius: 0,
          lineTension: 0,
          borderColor: '#0000',
          borderWidth: 1,
          data: []
        }, {
          label: 'Confidence Interval (high)',
          // backgroundColor: '#eee',
          backgroundColor: 'rgba(230,230,230,0.5)',
          fill: 1, // Fill between this dataset and dataset[1], i.e. between low & hi CI
          pointRadius: 0,
          lineTension: 0,
          borderColor: '#0000',
          borderWidth: 0,
          data: []
        }]
      }

      this.mainIndexPlot = new Chart(this.$refs.lpiplot.getContext('2d'), {
        type: 'line',
        data: data,
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false
            }
          },
          maintainAspectRatio: false,
          scales: {
            yAxis: {
              display: true,
              position: 'left',
              grid: {
                display: true
              },
              ticks: {
                callback: function(label, index, labels) {
                  // Force labels to always show one decimal place
                  return (+label).toFixed(1)
                }
              }
            }
          }
        }
      })
    },
    updateMainIndexPlot() {
      let plotData = this.mainIndexPlot.data
      plotData.labels = []
      plotData.datasets.forEach(x => x.data = [])

      this.trendData = null

      var token = this.updateMainIndexPlot.token = {}
      var stale = () => this.updateMainIndexPlot.token != token

      return api.lpiRunData(this.getFilterString(), this.selectedYear.value, 'txt').then((data) => {
        if(stale()) {
          return
        }
        if(data && data.indexOf('"LPI_final"') === 0) {
          this.trendData = data
          // format:
          // "LPI_final" "CI_low" "CI_low"
          // "1980" float float float

          let series = data.split('\n')
            .slice(1) // Ignore first line
            .filter(line => line.trim().length > 0 && !/NA/.test(line)) // Ignore empty or NA lines
            .map(line => line.split(' '))

          plotData.labels = series.map(x => parseInt(x[0].replace(/"/g, '')))
          plotData.datasets[0].data = series.map(x => parseFloat(x[1]))
          plotData.datasets[1].data = series.map(x => parseFloat(x[2]))
          plotData.datasets[2].data = series.map(x => parseFloat(x[3]))

          // update lpi plot
          this.noLPI = false
          console.log(plotData)
          this.mainIndexPlot.update()
        } else {
          this.noLPI = true
        }
      }).catch((e) => {
        if(!stale()) {
          console.log(e)
          this.noLPI = true
        }
      })
    },
    createMonitoringConsistencyPlot() {
      let data = {
        datasets: [{
          label: 'count > 0',
          backgroundColor: '#333',
          borderColor: '#333',
          borderWidth: 1,
          data: [] },
        {
          label: 'count = 0',
          backgroundColor: '#ccc',
          borderColor: '#ccc',
          borderWidth: 1,
          data: [] }]
      }
      this.monitoringConsistencyPlot = new Chart(this.$refs.dotplot.getContext('2d'), {
        type: 'bubble',
        data: data,
        options: {
          animation: false,
          responsive: true,
          maintainAspectRatio: false,
          tooltips: {
            mode: 'point'
          },
          plugins: {
            tooltip: {
              callbacks: {
                label(context) {
                  return context.label + ' (' + context.parsed.x + ')'
                }
              }
            }
          },
          scales: {
            yAxis: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Sites (time series)'
              }
            },
            xAxis: {
              type: 'linear',
              ticks: {
                callback: (label, index, labels) => '' + label
              }
            }
          }
        }
      })
    },
    createSummaryPlot() {
      this.summaryPlotData = {
        datasets: [{
          label: 'Number of taxa',
          xAxisID: 'year',
          yAxisID: 'numTaxa',
          borderColor: '#58899e',
          backgroundColor: '#58899e',
          data: []
        }, {
          label: 'Number of time series',
          xAxisID: 'year',
          yAxisID: 'numTimeSeries',
          borderColor: '#a3c489',
          backgroundColor: '#a3c489',
          data: []
        }]
      }
    },
    updateMonitoringConsistencyAndSummaryPlot() {
      const filterParams = this.getFilterParams()
      filterParams['format'] = 'plot'

      this.monitoringConsistencyPlot.data.datasets.forEach(x => x.data = [])
      this.summaryPlotData.datasets.forEach(x => x.data = [])

      return api.lpiPlot(filterParams).then((data) => {
          this.noData = data['dotplot'].length === 0

          var dotPlotData = data['dotplot']
          var plotData = this.monitoringConsistencyPlot.data

          dotPlotData.forEach(function(timeSeries, i) {
            timeSeries.forEach(function(value) {
              var year = value[0]
              var count = value[1]
              plotData.datasets[count === 0 ? 1 : 0].data.push({
                x: year,
                y: i + 1,
                r: 1
              })
            })
          })

          // summary plot
          var taxaCountData = data['summary']['taxa']
          var timeSeriesCountData = data['summary']['timeseries']
          var year = 0
          for (year in taxaCountData) {
            this.summaryPlotData.datasets[0].data.push({'x': +year, 'y': +taxaCountData[year]})
          }
          for (year in timeSeriesCountData) {
            this.summaryPlotData.datasets[1].data.push({'x': +year, 'y': +timeSeriesCountData[year]})
          }

          this.monitoringConsistencyPlot.update()
          this.refreshSummaryPlot() // note: this.summaryPlot.update() will cause exception as the axis might be change
        })
    },
    updatePlots() {
      this.loadingData = true
      Promise.all([
        this.updateMainIndexPlot(),
        this.updateMonitoringConsistencyAndSummaryPlot(),
      ]).finally(x => {
        this.loadingData = false
      })
    },
    updateMap() {
      // intensity plot
      this.loadingMap = true

      // using lpi wide table per Elisa'request
      // filterParams.source = 'lpi_wide_table'

      api.intensityPlot(this.getFilterParams()).then((data) => {
        console.log('--loading map data----')

        var surveyData = []
        data.forEach(function(timeSeries) {
          var lat = timeSeries[1]
          var long = timeSeries[0]
          var yearCounts = timeSeries[2]
          yearCounts.forEach(function(yearCount) {
            surveyData.push({
              lat: lat,
              long: long,
              count: yearCount[1],
              year: yearCount[0]
            })
          })
        })


        var counts = pluck(surveyData, 'value')

        // A scaling factor (/20) is chosen for aesthetic reasons.
        // Previously we were stacking points from many years on top of each other on the map, but
        // for performance reasons I have now combined all years into a single point (see 'fast_mode' in lpi_data.py).
        // This resulted in the heatmap being very faint compared to before, this scaling factor increases the intensity.
        this.heatmapLayer.setData({
          min: min(counts),
          max: max(counts) / 20,
          data: surveyData
        })
        // this.map.invalidateSize()
      }).finally(() => {
        this.loadingMap = false
      })
    },
    updateMapAndPlots() {
      this.updatePlots()
      this.updateMap()
    },
    downloadCSV: function() {
      var filterParams = this.getFilterParams()
      filterParams['format'] = 'zip'
      filterParams['data_filename'] = "tsx-aggregated-data-" + this.filterFilenamePart + ".csv"
      filterParams['download'] = "tsxdata.zip"
      var url = api.lpiDownloadURL(filterParams)
      window.open(url)
    },
    downloadTrend: function(evt) {
      var a = document.createElement('a');
      a.href = this.downloadTrendURL;
      a.download = "tsx-trend-" + this.filterFilenamePart + ".txt"
      a.click();
      if(evt.shiftKey) {
        this.downloadPlotData();
      }
    },
    downloadPlotData: function() {
      function quote(v) {
        if(typeof v === "string" && v.match(/["\n\r]/)) {
          return JSON.stringify(v)
        } else {
          return v
        }
      }

      function csv(rows) {
        return rows.map(row => row.map(quote).join(',')).join('\n')
      }

      function download(text, filename) {
        var dl = document.createElement("a")
        dl.href="data:text/plain,"+encodeURIComponent(text)
        dl.setAttribute("download", filename)
        dl.click();
      }

      async function save(name, params) {
        var data = await fetch("https://tsx.org.au/tsxapi/lpi-data/plot?" + params)
        var json = await data.json();

        var rows = json.dotplot.flatMap((a, i) => [a.map(b => [i, b[0], b[1]])]).flat()
        rows = [["TimeSeries", "Year", "NonZeroCount"]].concat(rows)

        download(csv(rows), "tsx-dotplot-" + name + ".csv");

        download(csv([["Year", "NumberOfTimeSeries"]].concat(Object.entries(json.summary.timeseries))), "tsx-time-series-" + name + ".csv")
        download(csv([["Year", "NumberOfTaxa"]].concat(Object.entries(json.summary.taxa))), "tsx-taxa-" + name + ".csv")

        // data = await fetch("https://tsx.org.au/tsxapi/lpi-data/intensity?" + params)
        // json = await data.json()
        // download(csv([["Lat", "Lon", "NumberOfSurveys"]].concat(json.map(x => [x[0], x[1], x[2][0][1]]))), prefix + "-intensity.csv")
      }

      save(this.filterFilenamePart, this.getFilterParams())
    },
    viewDataSummary: function() {
      var filterParams = this.getFilterParams()
      var url = api.lpiSummaryURL(filterParams)
      window.open(url)
    },
    acceptWarning: function() {
      localStorage.setItem('hasAcceptedWarning', true)
      this.hasAcceptedWarning = true
    },
    goBack: function() {
      window.history.back()
    },
    getFilterParams: function() {
      var filterParams = {}
      filterParams['reference_year'] = this.selectedYear.value

      function addParam(key, selectedItem) {
        if(selectedItem.value !== 'None') {
          filterParams[key] = selectedItem.value
        }
      }

      if(this.prioritySelected) {
        filterParams['priority'] = '1'
        addParam('management', this.selectedManagement)
      } else {
        addParam('tgroup', this.selectedIndex)
        addParam('group', this.selectedGroup)
        addParam('subgroup', this.selectedSubgroup)
        addParam('state', this.selectedState)
        addParam('statusauth', this.selectedStatusAuthority)
        addParam('status', this.selectedStatus)
        if(this.selectedIndex.value === 'Mammals' || this.selectedIndex.value === 'Plants') {
          addParam('management', this.selectedManagement)
        }
      }

      return filterParams
    },
    getFilterString: function() {
      var components

      if(this.prioritySelected) {
        components = [
          ['management', this.selectedManagement],
          ['priority', {value: 1}]
        ]
      } else {
        components = [
          ['tgroup', this.selectedIndex],
          ['group', this.selectedGroup],
          ['subgroup', this.selectedSubgroup],
          ['state', this.selectedState],
          ['statusauth', this.selectedStatusAuthority],
          ['status', this.selectedStatus],
          ['management', this.selectedIndex.value === 'Mammals' || this.selectedIndex.value === 'Plants' ? this.selectedManagement : noneOption]
        ]
      }

      return components.map(function(pair) {
        var key = pair[0]
        var value = pair[1].value

        return value === 'None' ? '' : key + '-' + value + '_'
      }).join('')
    },
    // refresh summary plot
    refreshSummaryPlot: function() {
      if (this.summaryPlot) {
        this.summaryPlot.destroy()
      }
      // create new one
      this.summaryPlot = new Chart(this.$refs.sumplot.getContext('2d'), {
        type: 'scatter',
        data: this.summaryPlotData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          hoverMode: 'nearest',
          intersect: true,
          plugins: {
            tooltip: {
              callbacks: {
                label(context) {
                  return '(' + context.parsed.x + ', ' + context.parsed.y + ')'
                }
              }
            }
          },
          scales: {
            year: {
              position: 'bottom',
              // gridLines: {
              //   zeroLineColor: 'rgba(0,0,0,1)'
              // },
              ticks: {
                callback: (label, index, labels) => '' + label
              }
            },
            numTaxa: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Number of taxa'
              },
              // ticks: {
              //   // precision: 1 // Doesn't seem to work (contrary to documentation) so we use callback as a workaround
              //   callback: function(label, index, labels) {
              //     return Math.floor(label) === label ? label : ''
              //   }
              // }
            },
            numTimeSeries: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Number of time series'
              },
              grid: {
                display: false
              },
              // ticks: {
              //   // See comment for other axis
              //   callback: function(label, index, labels) {
              //     return Math.floor(label) === label ? label : ''
              //   }
              // }
            }
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
<style scoped>
  .label {
    color: #fff;
  }
  h4 {
    /*margin-top: 0.5em;*/
    /*margin-left: 1em;*/
  }
  .heatmap-div {
    width: 100%;
    height: 25.5em;
    z-index:1;
  }
  .heatmap-spinner{
    z-index:2;
    position:absolute;
    top: 0.6em;
    right: 4em;
  }
  /* Important: the following line fixes the charts not resizing responsively */
  .tile {
    min-width: 0;
  }
  .tile.card {
    flex-basis: 22.5em;
    max-height: 22.5em;
    height: 22.5em;
    padding: 1em;
  }
  .plot-container {
    position: relative;
    height: 18em;
  }
  .tile.card.map-tile {
    padding: 0;
    padding-top: 1em;
  }
  .tile.card.map-tile h4 {
    margin-left: 1em;
  }

  .info-icon {
    color: #aaa;
    position: absolute;
    top: 0.7em;
    right: 1em;
    font-size: 120%;
  }
  .popup-content {
    max-width: 30em;
    text-align: left;
  }
  .popup-content p {
    margin-bottom: 1em;
  }
  .popup-content ol {
    padding-left: 1em;
  }
  .popup-content li {
    margin-bottom: 0.5em;
  }
  @media screen and (min-width: 768px) {
    .ie11-bugfix {
      /* Fix flexbox bug */
      height: 48em;
    }
  }
</style>

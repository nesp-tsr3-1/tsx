<template>
  <div class='plot content'>
    <h3 class='title'>Intensity Plots</h3>
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
        </div>
      </div>

      <div class="modal is-active" v-show='loadingData'>
        <div class="modal-background"></div>
        <div class="modal-card">
          <section class="modal-card-body">
            <spinner size='large' message='Loading data....'></spinner>
          </section>
        </div>
      </div>

        <div class="tile card">
          <!-- vue-slider min=1960 max=2005></vue-slider -->
          <div id='intensityplot1' ref='intensityplot1' class='heatmap-div'></div>
        </div>
        <div class="tile card">
          <!-- vue-slider min=1960 max=2005></vue-slider -->
          <div id='intensityplot2' ref='intensityplot2' class='heatmap-div'></div>
        </div>
      

      <div class="tile is-child" v-show="noData">
        <p style="margin: 0.8em">(No data to show)</p>
      </div>
    </div>
  </div>
</template>
<script>
import * as api from '@/api'
import Spinner from 'vue-simple-spinner'
import L from 'leaflet'
import HeatmapOverlay from 'heatmap.js/plugins/leaflet-heatmap/leaflet-heatmap.js'
export default {
  name: 'Intensity',
  components: {
    Spinner
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
      // is loading data
      loadingData: false,
      // need to query LPI rest service
      queryLPIData: true,
      // no data to show
      noData: true,
      // prioritySelected
      prioritySelected: false,
      // heatmap
      // intensity plot1
      heatmapLayer1: null,
      heatmapDataSet1: {max: 0, min: 0, data: []},
      map1: null,
      // intensity plot2
      heatmapLayer2: null,
      heatmapDataSet2: {max: 0, min: 0, data: []},
      map2: null
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
    // -------intensity plot ----------------
    var baseLayer1 = L.tileLayer(
      'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    var baseLayer2 = L.tileLayer(
      'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    // TODO: might need to tweak some of these
    var cfg = {
      'radius': 0.5,
      'maxOpacity': 0.8,
      'minOpacity': 0,
      'blur': 0.75,
      'scaleRadius': true,
      'useLocalExtrema': false,
      latField: 'lat',
      lngField: 'long',
      valueField: 'count'
    }
    this.heatmapLayer1 = new HeatmapOverlay(cfg)
    this.map1 = new L.Map('intensityplot1', {
      center: new L.LatLng(-20.917574, 142.702789),
      zoom: 4,
      layers: [baseLayer1, this.heatmapLayer1]
    })
    this.heatmapLayer2 = new HeatmapOverlay(cfg)
    this.map2 = new L.Map('intensityplot2', {
      center: new L.LatLng(-20.917574, 142.702789),
      zoom: 4,
      layers: [baseLayer2, this.heatmapLayer2]
    })

    // this is a hack so that leaflet displays properlly
    setTimeout(function() {
      that.map1.invalidateSize()
      that.map2.invalidateSize()
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
    }
  },
  computed: {
    filterParams() {
      return this.getFilterParams()
    }
  },
  methods: {
    updatePlot: function() {
      this.loadingData = true
      // clear existing data
      this.heatmapDataSet1.data = []
      this.heatmapDataSet1.max = 0
      this.heatmapDataSet1.min = 10000
      this.heatmapDataSet2.data = []
      this.heatmapDataSet2.max = 0
      this.heatmapDataSet2.min = 10000
      // filters
      var filterParams = this.getFilterParams()
      var that = this
      if(this.queryLPIData) {
        // ping api first
        api.lpiPlot(filterParams).then((data) => {
          this.noData = data['dotplot'].length === 0
          var intensityPlotData = data['intensity']
          intensityPlotData.forEach(function(timeSerie) {
            that.heatmapDataSet1.data.push({
              'lat': timeSerie[0],
              'long': timeSerie[1],
              'count': timeSerie[2]
            })
            if (timeSerie[2] > that.heatmapDataSet1.max) that.heatmapDataSet1.max = timeSerie[2]
            if (timeSerie[2] < that.heatmapDataSet1.min) that.heatmapDataSet1.min = timeSerie[2]
          })
          that.heatmapLayer1.setData(that.heatmapDataSet1)
          that.map1.invalidateSize()
        }).finally(() => {
          this.queryLPIData = false
          that.loadingData = false
        })
      }
      // intensity plot
      api.intensityPlot(filterParams).then((data) => {
        data.forEach(function(timeSerie) {
          that.heatmapDataSet2.data.push({
            'lat': timeSerie[1],
            'long': timeSerie[0],
            'count': timeSerie[2]
          })
          if (timeSerie[2] > that.heatmapDataSet2.max) that.heatmapDataSet2.max = timeSerie[2]
          if (timeSerie[2] < that.heatmapDataSet2.min) that.heatmapDataSet2.min = timeSerie[2]
        })
        that.heatmapLayer2.setData(that.heatmapDataSet2)
        that.map2.invalidateSize()
      })
      // ------- heatmap -------------
    }, // end updatePlot function
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
    }
  }
}
</script>

<style src='leaflet/dist/leaflet.css'>
</style>
<style>
  .heatmap-div {
    width: 100%;
    height: 100%;
  }
</style>

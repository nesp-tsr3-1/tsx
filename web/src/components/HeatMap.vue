<template>
  <div style="width: 100%;
              height: 100%;
              position: relative;">
    <div ref="map" style="width: 100%; height: 100%; flex: none; position: absolute;"></div>
    <div v-if="loading" style="width: 100%;
              height: 100%;
              display: flex;
              justify-content: center;
              align-items: center;
              background: rgba(0,0,0,0.3);
              position: relative;
              z-index: 10000">
      <Spinner/>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import HeatmapOverlay from 'heatmap.js/plugins/leaflet-heatmap/leaflet-heatmap.js'
import Spinner from '../../node_modules/vue-simple-spinner/src/components/Spinner.vue'

export default {
  name: 'HeatMap',
  components: {
    Spinner
  },
  data () {
    return {
      map: null,
      heatmapLayer: null
    }
  },
  computed: {
  },
  watch: {
    heatmapData() {
      this.updateHeatmap()
    }
  },
  mounted () {
    var baseLayer = L.tileLayer(
      '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 5
      }
    )
    this.heatmapLayer = new HeatmapOverlay({
      fullscreenControl: true,
      radius: 0.45,
      maxOpacity: 0.8,
      minOpacity: 0.5,
      blur: 0.75,
      scaleRadius: true,
      useLocalExtrema: false,
      latField: 'lat',
      lngField: 'lon',
      valueField: 'c',
      gradient: {0.25: 'rgb(0,94,255)', 0.5: 'rgb(0,0,255)', 0.85: 'rgb(163,0,255)', 1.0: 'rgb(255,0,255)'}
    })
    this.map = new L.Map(this.$refs.map, {
      center: new L.LatLng(-25.917574, 132.702789),
      zoom: 3,
      layers: [baseLayer, this.heatmapLayer]
    })
    this.updateHeatmap()
  },
  created () {

  },
  methods: {
    updateHeatmap() {
      if(this.heatmapLayer) {
        if(this.heatmapData && this.heatmapData.length) {
          this.heatmapLayer.setData({ min: 0, max: 1, data: this.heatmapData })
          this.map.fitBounds(this.heatmapData.map(x => [x.lat, x.lon]))
        } else {
          this.heatmapLayer.setData({ min: 0, max: 1, data: []})
        }
      }
    }
  },
  props: ['heatmapData', 'loading']
}
</script>

<style>

</style>
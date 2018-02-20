import Vue from 'vue'
import Router from 'vue-router'
import ImportHome from '@/components/ImportHome'
import ImportEdit from '@/components/ImportEdit'
import Plot from '@/components/Plot'
import TSX from '@/components/TSX'
import Intensity from '@/components/Intensity'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'ImportHome',
      component: ImportHome
    },
    {
      path: '/import/:id',
      name: 'ImportEdit',
      component: ImportEdit
    },
    {
      path: '/plot',
      name: 'Plot',
      component: Plot
    },
    {
      path: '/tsx',
      name: 'TSX',
      component: TSX
    },
    {
      path: '/intensity',
      name: 'Intensity',
      component: Intensity
    }
  ]
})

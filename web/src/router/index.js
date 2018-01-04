import Vue from 'vue'
import Router from 'vue-router'

import ImportHome from '@/components/ImportHome'
import ImportEdit from '@/components/ImportEdit'
import Plot from '@/components/Plot'
import LPI from '@/components/LPI'

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
      path: '/lpi',
      name: 'LPI',
      component: LPI
    }
  ]
})

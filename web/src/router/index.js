import Vue from 'vue'
import Router from 'vue-router'

import ImportHome from '@/components/ImportHome'
import ImportEdit from '@/components/ImportEdit'

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
    }
  ]
})

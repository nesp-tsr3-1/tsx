import Vue from 'vue'
import Router from 'vue-router'
import ImportHome from '@/components/ImportHome'
import ImportEdit from '@/components/ImportEdit'
import Plot from '@/components/Plot'
import TSX from '@/components/TSX'
import Intensity from '@/components/Intensity'
import Login from '@/components/Login'
import SignUp from '@/components/SignUp'
import * as api from '@/api'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/logout',
      beforeEnter: (to, from, next) => {
        console.log('beforeEnter!')
        api.logout().finally(() => next('/'))
      }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/signup',
      name: 'Sign Up',
      component: SignUp
    },
    {
      path: '/import',
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
      path: '/',
      name: 'TSX',
      component: TSX
    },
    {
      path: '/tsx',
      redirect: '/'
    },
    {
      path: '/intensity',
      name: 'Intensity',
      component: Intensity
    }
  ]
})

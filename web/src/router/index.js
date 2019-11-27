import Vue from 'vue'
import Router from 'vue-router'
import SourceHome from '@/components/SourceHome'
import SourceEdit from '@/components/SourceEdit'
import SourceView from '@/components/SourceView'
import UserManage from '@/components/UserManage'
import Plot from '@/components/Plot'
import TSX from '@/components/TSX'
import Intensity from '@/components/Intensity'
import Login from '@/components/Login'
import SignUp from '@/components/SignUp'
import ResetPassword from '@/components/ResetPassword'
import * as api from '@/api'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/logout',
      name: 'Logout',
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
      path: '/reset_password',
      name: 'Reset Password',
      component: ResetPassword
    },
    {
      path: '/source',
      name: 'SourceHome',
      component: SourceHome
    },
    {
      path: '/source/edit/:id',
      name: 'SourceEdit',
      component: SourceEdit
    },
    {
      path: '/source/:id',
      name: 'SourceView',
      component: SourceView
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
    },
    {
      path: '/manager-users',
      name: 'UserManage',
      component: UserManage
    }
  ]
})

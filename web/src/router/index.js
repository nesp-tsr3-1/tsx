import { createRouter, createWebHashHistory } from 'vue-router'
import SourceHome from '../components/SourceHome.vue'
import SourceEdit from '../components/SourceEdit.vue'
import SourceView from '../components/SourceView.vue'
import UserManage from '../components/UserManage.vue'
// import Plot from '../components/Plot.vue'
import TSX from '../components/TSX.vue'
// import Intensity from '../components/Intensity.vue'
import Login from '../components/Login.vue'
import SignUp from '../components/SignUp.vue'
import ResetPassword from '../components/ResetPassword.vue'
import DataSubsetDownloads from '../components/DataSubsetDownloads.vue'
import * as api from '../api'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/logout',
      name: 'Logout',
      beforeEnter: (to, from, next) => {
        api.logout().finally(() => {
          api.refreshCurrentUser()
          next('/login')
        })
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
      path: '/import',
      redirect: '/source'
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
    // {
    //   path: '/plot',
    //   name: 'Plot',
    //   component: Plot
    // },
    {
      path: '/',
      name: 'TSX',
      component: TSX
    },
    {
      path: '/tsx',
      redirect: '/'
    },
    // {
    //   path: '/intensity',
    //   name: 'Intensity',
    //   component: Intensity
    // },
    {
      path: '/manager-users',
      name: 'UserManage',
      component: UserManage
    },
    {
      path: '/downloads',
      name: 'DataSubsetDownloads',
      component: DataSubsetDownloads
    }
  ]
})

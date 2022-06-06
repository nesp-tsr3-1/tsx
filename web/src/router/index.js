import { createRouter, createWebHashHistory } from 'vue-router'
import SourceHome from '../components/SourceHome.vue'
import SourceEdit from '../components/SourceEdit.vue'
import SourceView from '../components/SourceView.vue'
import UserManage from '../components/UserManage.vue'
import ProgramManage from '../components/ProgramManage.vue'
import ProgramEdit from '../components/ProgramEdit.vue'
import ProgramView from '../components/ProgramView.vue'
import TSX from '../components/TSX.vue'
import Login from '../components/Login.vue'
import SignUp from '../components/SignUp.vue'
import ResetPassword from '../components/ResetPassword.vue'
import DataSubsetDownloads from '../components/DataSubsetDownloads.vue'
import * as api from '../api'

const router = createRouter({
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
      path: '/manager-users',
      name: 'UserManage',
      component: UserManage
    },
    {
      path: '/manage_programs',
      name: 'ProgramManage',
      component: ProgramManage
    },
    {
      path: '/program/edit/:id',
      name: 'ProgramEdit',
      component: ProgramEdit
    },
    {
      path: '/program/:id',
      name: 'ProgramView',
      component: ProgramView
    },
    {
      path: '/downloads',
      name: 'DataSubsetDownloads',
      component: DataSubsetDownloads
    }
  ]
})

// Set custom title for TSX visualisation page
router.beforeEach((to, from, next) => {
  try {
    var title = (to.name === 'TSX') ? 'The Australian Threatened Species Index 2020' : 'The Australian Threatened Species Index'
    document.getElementById('main-title').textContent = title
  } finally {
    next()
  }
})

export default router

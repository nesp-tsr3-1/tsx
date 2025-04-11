import { createRouter, createWebHistory } from 'vue-router'
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
import UserEdit from '../components/UserEdit.vue'
import CustodianFeedbackHome from '../components/CustodianFeedbackHome.vue'
import CustodianFeedbackDataset from '../components/CustodianFeedbackDataset.vue'
import CustodianFeedbackForm from '../components/CustodianFeedbackForm.vue'
import * as api from '../api'

const router = createRouter({
  history: createWebHistory('/data'),
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
      path: '/datasets',
      name: 'SourceHome',
      component: SourceHome
    },
    {
      path: '/datasets/edit/:id',
      name: 'SourceEdit',
      component: SourceEdit
    },
    {
      path: '/datasets/:id',
      name: 'SourceView',
      component: SourceView
    },
    {
      path: '/manage_users',
      name: 'UserManage',
      component: UserManage
    },
    {
      path: '/manage_programs',
      name: 'ProgramManage',
      component: ProgramManage
    },
    {
      path: '/programs/edit/:id',
      name: 'ProgramEdit',
      component: ProgramEdit
    },
    {
      path: '/programs/:id',
      name: 'ProgramView',
      component: ProgramView
    },
    {
      path: '/downloads',
      name: 'DataSubsetDownloads',
      component: DataSubsetDownloads
    },
    {
      path: '/manage_account',
      name: 'UserEdit',
      component: UserEdit
    },
    {
      path: '/custodian_feedback',
      name: 'CustodianFeedbackHome',
      component: CustodianFeedbackHome
    },
    {
      path: '/custodian_feedback/:id',
      name: 'CustodianFeedbackDataset',
      component: CustodianFeedbackDataset
    },
    {
      path: '/custodian_feedback/form/:id/edit',
      name: 'EditCustodianFeedbackForm',
      component: CustodianFeedbackForm
    },
    {
      path: '/custodian_feedback/form/:id',
      name: 'ViewCustodianFeedbackForm',
      component: CustodianFeedbackForm,
      props: { viewOnly: true }
    },
    {
      path: '/',
      redirect: '/datasets'
    },
    {
      // legacy URL redirect
      path: '/source',
      redirect: '/datasets'
    }
  ]
})

export default router

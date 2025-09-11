// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import { createApp } from 'vue'
import App from '../src/DataInterfaceApp.vue'
import router from '../src/router'
import autofocus from 'vue-autofocus-directive'
import UserNav from '../src/components/UserNav.vue'

const app = createApp(App)
app.use(router)
app.directive('autofocus', autofocus)
app.component('UserNav', UserNav)
app.mount('#app')

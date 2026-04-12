import { createRouter, createWebHistory } from 'vue-router'
import Admin from './pages/Admin.vue'
import Client from './pages/Client.vue'

const routes = [
  { path: '/', component: Admin },
  { path: '/client', component: Client },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
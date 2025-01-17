import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
import ChatDB from '../views/ChatDB.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  },
  {
    path: '/chat',
    name: '一个凑合的聊天仪表盘',
    component: ChatDB
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
import ChatDB from '../views/ChatDB.vue'

const routes = [
  {
    path: '/',
    redirect: '/chat'
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
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('../views/TrainingView.vue'),
    meta: {
      title: '训练数据管理'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

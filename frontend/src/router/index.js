import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ===== 游戏全屏模式 =====
  {
    path: '/',
    name: 'Intro',
    component: () => import('../views/IntroView.vue'),
  },
  {
    path: '/game',
    name: 'Game',
    component: () => import('../views/GameView.vue'),
  },

  // ===== 平台模式（侧边栏布局） =====
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
  },
  {
    path: '/link-check',
    name: 'LinkCheck',
    component: () => import('../views/LinkCheckView.vue'),
  },
  {
    path: '/simulation',
    name: 'Simulation',
    component: () => import('../views/SimulationView.vue'),
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },

  // 兜底重定向到聊天
  {
    path: '/:pathMatch(.*)*',
    redirect: '/chat',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

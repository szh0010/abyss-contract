import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUser, clearAuth } from '../services/http'

const routes = [
  // 登录页（唯一公开）
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, layout: 'blank' },
  },

  // 根路径：登录则去 /chat，否则去 /login
  {
    path: '/',
    redirect: () => (getToken() && getUser() ? '/chat' : '/login'),
  },

  // 平台（需要登录）
  { path: '/chat', name: 'Chat', component: () => import('../views/ChatView.vue') },
  { path: '/link-check', name: 'LinkCheck', component: () => import('../views/LinkCheckView.vue') },
  // 旧「情景模拟」中间页已废弃，统一汇入新作战大厅
  { path: '/simulation', redirect: '/game' },

  // 游戏全屏（需要登录）
  { path: '/game/intro', name: 'Intro', component: () => import('../views/IntroView.vue') },
  { path: '/game',       name: 'Abyss', component: () => import('../views/AbyssGame.vue') },
  // 旧入口向下兼容：统一汇入新关卡大厅
  { path: '/game/home', redirect: '/game' },
  { path: '/game/play', redirect: '/game' },

  // 兜底
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 全局鉴权守卫：
 * - 公开路由（meta.public = true）直接放行
 * - 其余路由必须同时存在 token + user；否则清理残留凭证后跳 /login
 * - 保留 redirect 参数，登录后可原路返回
 */
router.beforeEach((to) => {
  const isPublic = to.matched.some((r) => r.meta.public)
  if (isPublic) return true

  const token = getToken()
  const user = getUser()
  if (!token || !user) {
    // 只要缺一个就视为未登录，顺手清掉脏状态防死循环
    if (token || user) clearAuth()
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  return true
})

// 已登录再访问 /login 时直接送回 /chat
router.beforeEach((to) => {
  if (to.name === 'Login' && getToken() && getUser()) {
    return { path: '/chat' }
  }
  return true
})

export default router

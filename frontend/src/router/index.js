import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

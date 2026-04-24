import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/game',
    name: 'Game',
    component: () => import('../views/GameView.vue'),
    beforeEnter: (to, from, next) => {
      // Prevent direct access without going through intro
      if (!from.name && !sessionStorage.getItem('abyss_player_name')) {
        next('/')
      } else {
        next()
      }
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

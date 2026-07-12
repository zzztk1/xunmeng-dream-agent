import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/AuthView.vue'), meta: { guest: true } },
  { path: '/register', name: 'register', component: () => import('../views/AuthView.vue'), meta: { guest: true } },
  { path: '/showcase', name: 'showcase', component: () => import('../views/ExperienceView.vue'), meta: { immersive: true, showcase: true } },
  { path: '/insights', name: 'insights', component: () => import('../views/InsightsView.vue'), meta: { requiresAuth: true } },
  { path: '/capture', name: 'capture', component: () => import('../views/CaptureView.vue') },
  { path: '/dream/:id/play', name: 'experience', component: () => import('../views/ExperienceView.vue'), meta: { immersive: true, requiresAuth: true } },
  { path: '/dream/:id', name: 'detail', component: () => import('../views/DetailView.vue'), meta: { requiresAuth: true } },
  { path: '/library', name: 'library', component: () => import('../views/LibraryView.vue'), meta: { requiresAuth: true } },
  { path: '/calendar', name: 'calendar', component: () => import('../views/CalendarView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.ready) await auth.fetchMe()
  if (to.meta.requiresAuth && !auth.isAuthed) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guest && auth.isAuthed) {
    return { name: 'home' }
  }
})

export default router

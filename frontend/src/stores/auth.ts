import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'
import type { User } from '../types'

export const useAuth = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const ready = ref(false) // 是否已完成首次 me() 探测

  const isAuthed = computed(() => !!user.value)

  async function fetchMe() {
    try {
      user.value = await api.me()
    } catch {
      user.value = null
    } finally {
      ready.value = true
    }
  }
  async function login(username: string, password: string) {
    user.value = await api.login(username, password)
  }
  async function register(username: string, password: string, displayName?: string) {
    user.value = await api.register(username, password, displayName)
  }
  async function logout() {
    try { await api.logout() } finally { user.value = null }
  }

  return { user, ready, isAuthed, fetchMe, login, register, logout }
})

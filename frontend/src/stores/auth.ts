import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as identity from '../api/identity'
export const useAuth = defineStore('auth', () => {
  const user = ref<identity.User | null>(null)
  function clear() {
    user.value = null
    sessionStorage.removeItem('access_token')
  }
  async function restore() {
    if (!sessionStorage.getItem('access_token')) return false
    try {
      user.value = await identity.me()
      return true
    } catch {
      clear()
      return false
    }
  }
  async function signIn(username: string, password: string) {
    const result = await identity.login({ username, password })
    sessionStorage.setItem('access_token', result.access_token)
    user.value = await identity.me()
  }
  window.addEventListener('auth-expired', () => {
    clear()
    if (location.pathname !== '/login') location.assign('/login')
  })
  return { user, clear, restore, signIn }
})

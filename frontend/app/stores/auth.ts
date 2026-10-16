import { defineStore } from 'pinia'
import type { User } from '~/types/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isStaff = computed(() => user.value?.role === 'staff' || user.value?.role === 'admin')

  const setUser = (u: User | null) => { user.value = u }
  const clear = () => { user.value = null }

  return { user, isAuthenticated, isAdmin, isStaff, setUser, clear }
})

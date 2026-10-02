import { defineStore } from 'pinia'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
}

export const useUiStore = defineStore('ui', () => {
  const isMobileMenuOpen = ref(false)
  const notifications = ref<Notification[]>([])

  const toggleMobileMenu = () => { isMobileMenuOpen.value = !isMobileMenuOpen.value }
  const closeMobileMenu = () => { isMobileMenuOpen.value = false }

  /**
   * Push a notification onto the stack.
   *
   * @warning Do NOT call during SSR setup() or template interpolation.
   * Uses `crypto.randomUUID()` which produces different IDs on server vs
   * client, causing hydration mismatch. Safe for user-triggered actions
   * (button clicks, API error handlers, form submissions post-mount).
   */
  const pushNotification = (n: Omit<Notification, 'id'>) => {
    notifications.value.push({ ...n, id: crypto.randomUUID() })
  }
  const dismissNotification = (id: string) => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return {
    isMobileMenuOpen, notifications,
    toggleMobileMenu, closeMobileMenu,
    pushNotification, dismissNotification,
  }
})

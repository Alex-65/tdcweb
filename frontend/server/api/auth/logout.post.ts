import { defineEventHandler } from 'h3'

export default defineEventHandler(async (event) => {
  try {
    await flaskFetch('/api/auth/logout', event, { method: 'POST' })
  } catch {
    // Even if Flask fails, clear our cookies to log the user out locally
  }
  clearAuthCookies(event)
  return { success: true }
})

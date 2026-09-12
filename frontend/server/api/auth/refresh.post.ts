import { defineEventHandler } from 'h3'
import type { ApiResponse } from '~/types/api'

interface FlaskRefreshPayload {
  access: string
  refresh: string
}

export default defineEventHandler(async (event) => {
  const refresh = getRefreshToken(event)
  if (!refresh) {
    throw createError({ statusCode: 401, statusMessage: 'No refresh token' })
  }

  // Flask envelope: { success: true, data: { access, refresh } }
  const response = await flaskFetch<ApiResponse<FlaskRefreshPayload>>('/api/auth/refresh', event, {
    method: 'POST',
    headers: { Authorization: `Bearer ${refresh}` },
  })

  setAccessCookie(event, response.data.access)
  setRefreshCookie(event, response.data.refresh)

  return { success: true }
})

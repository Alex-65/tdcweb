import { defineEventHandler } from 'h3'
import type { User } from '~/types/user'
import type { ApiResponse } from '~/types/api'

export default defineEventHandler(async (event) => {
  const hasAccess = event.context.flaskHeaders !== undefined
  if (!hasAccess) {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }

  // Flask envelope: { success: true, data: <User> }. Unwrap before
  // returning the conventional `{ user }` shape to the client.
  const response = await flaskFetch<ApiResponse<User>>('/api/auth/me', event)
  return { user: response.data }
})

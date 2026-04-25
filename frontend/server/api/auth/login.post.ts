import { defineEventHandler } from 'h3'
import { z } from 'zod'
import type { ApiResponse } from '~/types/api'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

interface FlaskLoginPayload {
  access: string
  refresh: string
  user: {
    id: number
    email: string
    username: string
    role: 'user' | 'staff' | 'admin'
  }
}

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, (input) => loginSchema.parse(input))

  // Flask wraps every response in `{ success: true, data: <payload> }` per
  // backend/app/utils/responses.py canonical envelope. The BFF unwraps
  // here so client never sees the envelope.
  const response = await flaskFetch<ApiResponse<FlaskLoginPayload>>('/api/auth/login', event, {
    method: 'POST',
    body,
  })

  setAccessCookie(event, response.data.access)
  setRefreshCookie(event, response.data.refresh)

  return { user: response.data.user }
})

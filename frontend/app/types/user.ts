/**
 * User identity + role types.
 *
 * Mirrors the user-facing fields of the MySQL `users` table (pdp-v2 §3.1),
 * minus `password_hash`. Fields use snake_case to match the Flask JSON
 * payload — we do NOT camelCase at the type boundary.
 *
 * Roles per CLAUDE.md § User Roles: guest (unauthenticated, no User
 * record) / user / staff / admin.
 */

export type UserRole = 'user' | 'staff' | 'admin'

export interface User {
  id: number
  email: string
  username: string
  avatar_name: string | null
  role: UserRole
  language: string
  email_verified: boolean
  email_notifications: boolean
  created_at: string
  last_login: string | null
}

export interface AuthResponse {
  user: User
}
